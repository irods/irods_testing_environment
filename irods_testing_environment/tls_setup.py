# grown-up modules
import json
import logging
import os

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dh, rsa
from cryptography.x509.oid import NameOID

# local modules
from . import context
from . import execute
from . import irods_config
from . import json_utils

def generate_tls_certificate_key(directory=None):
    logging.info('generating private key for signing certificate')

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    keyfile = os.path.join((directory or os.getcwd()), 'server.key')

    logging.info('writing private key to file [{}]'.format(keyfile))

    with open(keyfile, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
            ))

    return key, keyfile


def generate_tls_self_signed_certificate(key, directory=None):
    import datetime

    logging.info('generating self-signed certificate')

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u'US'),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u'North Carolina'),
        x509.NameAttribute(NameOID.LOCALITY_NAME, u'Chapel Hill'),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u'iRODS Consortium'),
    ])

    cert = x509.CertificateBuilder() \
               .subject_name(subject) \
               .issuer_name(issuer) \
               .public_key(key.public_key()) \
               .serial_number(x509.random_serial_number()) \
               .not_valid_before(datetime.datetime.utcnow()) \
               .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365)) \
               .add_extension(x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
                              critical=False) \
               .sign(key, hashes.SHA256())

    certfile = os.path.join((directory or os.getcwd()), 'server.crt')

    logging.info('writing cert to file [{}]'.format(certfile))

    with open(certfile, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))

    return certfile


def generate_tls_dh_params(generator=2, key_size=1024, directory=None):
    logging.info('generating dh params')

    parameters = dh.generate_parameters(generator=2, key_size=key_size)

    dhfile = os.path.join((directory or os.getcwd()), 'dhparams.pem')

    logging.info('writing dhparams to file [{}]'.format(dhfile))

    with open(dhfile, 'wb') as f:
        f.write(parameters.parameter_bytes(encoding=serialization.Encoding.PEM,
                                           format=serialization.ParameterFormat.PKCS3))

    return dhfile


def configure_tls_for_service_account(container, cert_file):
    """Configure TLS for the iRODS service account client environment.

    Arguments:
    container -- the docker.Container on which TLS will be configured
    cert_file -- path to the file in the container containing the self-signed cert
    """
    logging.warning(f'[{container.name}]: configuring TLS')

    # add certificate chain file, certificate key file, and dh parameters file to iRODS
    # service account environment file
    service_account_irods_env = os.path.join(context.irods_home(), '.irods', 'irods_environment.json')
    irods_env = json_utils.get_json_from_file(container, service_account_irods_env)

    logging.debug(f'[{container.name}: env before [{json.dumps(irods_env)}]')

    irods_env['irods_client_server_policy'] = 'CS_NEG_REQUIRE'
    irods_env['irods_ssl_ca_certificate_file'] = cert_file
    irods_env['irods_ssl_verify_server'] = 'cert'

    logging.debug(f'[{container.name}: env after [{json.dumps(irods_env)}]')

    json_utils.put_json_to_file(container, service_account_irods_env, irods_env)


def configure_tls_in_server_config(container, key_file, chain_file, dhparams_file, cert_file):
    """Configure TLS in server_config on the iRODS server.

    Arguments:
    container -- the docker.Container on which TLS will be configured
    key_file -- path to the file in the container containing the private key for the cert
    chain_file -- path to the file in the container containing the self-signed cert
    dhparams_file -- path to the file in the container containing the dhparams PEM file
    """
    from . import negotiation_key

    config = json_utils.get_json_from_file(container, context.server_config())

    logging.debug(f'[{container.name}: config before [{json.dumps(config)}]')

    config["client_server_policy"] = "CS_NEG_REQUIRE"
    config["tls_server"] = {
        "certificate_chain_file": chain_file,
        "certificate_key_file": key_file,
        "dh_params_file": dhparams_file,
    }
    config["tls_client"] = {
        "ca_certificate_file": cert_file,
        "verify_server": "cert"
    }

    json_utils.put_json_to_file(container, context.server_config(), config)

    logging.debug(f'[{container.name}: config after [{json.dumps(config)}]')

    negotiation_key.backup_file(container, context.core_re())
    negotiation_key.configure_tls_in_server(container, 'CS_NEG_REQUIRE')


def configure_tls_on_irods4_server(container,
                                   path_to_key_file_on_host,
                                   path_to_cert_file_on_host,
                                   path_to_dhparams_file_on_host):
    """Copy TLS files to the container and configure TLS on the iRODS 4 server.

    Arguments:
    container -- the docker.Container on which TLS will be configured
    path_to_key_file_on_host -- path to file on host containing the private key for the cert
    path_to_cert_file_on_host -- path to file on host containing the self-signed cert
    path_to_dhparams_file_on_host -- path to file on host containing the dhparams PEM file
    """
    from . import archive
    from . import negotiation_key

    key_file = os.path.join(context.irods_config(), 'server.key')
    dhparams_file = os.path.join(context.irods_config(), 'dhparams.pem')
    chain_file = os.path.join(context.irods_config(), 'chain.pem')
    cert_file = os.path.join(context.irods_config(), 'server.crt')

    stop_cmd = "python3 -c 'from scripts.irods.controller import IrodsController; IrodsController().stop()'"
    if execute.execute_command(container, stop_cmd, user='irods', workdir=context.irods_home()) != 0:
        raise RuntimeError(f"[{container.name}] failed to stop iRODS server before TLS configuration")

    logging.warning(f"[{container.name}] configuring TLS")

    archive.copy_files_in_container(container,
                                    [(path_to_key_file_on_host, key_file),
                                     (path_to_cert_file_on_host, chain_file),
                                     (path_to_cert_file_on_host, cert_file),
                                     (path_to_dhparams_file_on_host, dhparams_file)])

    # add certificate chain file, certificate key file, and dh parameters file to iRODS
    # service account environment file
    service_account_irods_env = os.path.join(context.irods_home(),
                                             '.irods', 'irods_environment.json')
    irods_env = json_utils.get_json_from_file(container, service_account_irods_env)

    logging.debug('env [{}] [{}]'.format(json.dumps(irods_env), container.name))

    irods_env['irods_client_server_policy'] = 'CS_NEG_REQUIRE'
    irods_env['irods_ssl_ca_certificate_file'] = cert_file
    irods_env['irods_ssl_certificate_chain_file'] = chain_file
    irods_env['irods_ssl_certificate_key_file'] = key_file
    irods_env['irods_ssl_dh_params_file'] = dhparams_file
    irods_env['irods_ssl_verify_server'] = 'cert'

    logging.debug('env [{}] [{}]'.format(json.dumps(irods_env), container.name))

    json_utils.put_json_to_file(container, service_account_irods_env, irods_env)

    # TODO: consider using a generator to restore the file here...
    negotiation_key.backup_file(container, context.core_re())
    negotiation_key.configure_tls_in_server(container, 'CS_NEG_REQUIRE')

    # start the server again
    start_cmd = "python3 -c 'from scripts.irods.controller import IrodsController; IrodsController().start()'"
    if execute.execute_command(container, start_cmd, user='irods', workdir=context.irods_home()) != 0:
        raise RuntimeError(f"[{container.name}] failed to start iRODS server after TLS configuration")

    logging.warning(f"[{container.name}] TLS configured successfully")


def configure_tls_on_server(container,
                            path_to_key_file_on_host,
                            path_to_cert_file_on_host,
                            path_to_dhparams_file_on_host):
    """Copy TLS files to the container and configure TLS on the iRODS server.

    Arguments:
    container -- the docker.Container on which TLS will be configured
    path_to_key_file_on_host -- path to file on host containing the private key for the cert
    path_to_cert_file_on_host -- path to file on host containing the self-signed cert
    path_to_dhparams_file_on_host -- path to file on host containing the dhparams PEM file
    """
    # If this is not an iRODS 5 server, use the old way of configuring TLS.
    version = irods_config.get_irods_version(container)
    if int(version[0]) < 5 and int(version[1]) < 90:
        return configure_tls_on_irods4_server(
            container, path_to_key_file_on_host, path_to_cert_file_on_host, path_to_dhparams_file_on_host)

    from . import archive
    from . import negotiation_key

    key_file = os.path.join(context.irods_config(), 'server.key')
    dhparams_file = os.path.join(context.irods_config(), 'dhparams.pem')
    chain_file = os.path.join(context.irods_config(), 'chain.pem')
    cert_file = os.path.join(context.irods_config(), 'server.crt')

    stop_cmd = "python3 -c 'from scripts.irods.controller import IrodsController; IrodsController().stop()'"
    if execute.execute_command(container, stop_cmd, user='irods', workdir=context.irods_home()) != 0:
        raise RuntimeError(f"[{container.name}] failed to stop iRODS server before TLS configuration")

    logging.warning(f"[{container.name}] configuring TLS")

    archive.copy_files_in_container(container,
                                    [(path_to_key_file_on_host, key_file),
                                     (path_to_cert_file_on_host, chain_file),
                                     (path_to_cert_file_on_host, cert_file),
                                     (path_to_dhparams_file_on_host, dhparams_file)])

    configure_tls_for_service_account(container, cert_file)

    configure_tls_in_server_config(container, key_file, chain_file, dhparams_file, cert_file)

    # start the server again
    start_cmd = "python3 -c 'from scripts.irods.controller import IrodsController; IrodsController().start()'"
    if execute.execute_command(container, start_cmd, user='irods', workdir=context.irods_home()) != 0:
        raise RuntimeError(f"[{container.name}] failed to start iRODS server after TLS configuration")

    logging.warning(f"[{container.name}] TLS configured successfully")


def configure_tls_in_zone(docker_client, compose_project):
    import concurrent.futures
    import tempfile

    # Each irods_environment.json file is describing the cert this client will use and why
    # they think it is good. The testing environment is using a self-signed certificate, so
    # the certificate, key, and dhparams should be generated ONCE and copied to each server.
    #tls_files_dir = tempfile.mkdtemp()
    key, key_file = generate_tls_certificate_key()
    cert_file = generate_tls_self_signed_certificate(key)
    dhparams_file = generate_tls_dh_params()

    try:
        rc = 0

        # Configure TLS on the catalog service providers first because communication with the
        # catalog service consumers depends on being able to communicate with the catalog
        # service provider. If TLS is not configured first on the catalog service provider
        # the catalog service consumers will not be able to communicate with it.
        csps = compose_project.containers(service_names=[
            context.irods_catalog_provider_service()])

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures_to_containers = {
                executor.submit(configure_tls_on_server,
                                docker_client.containers.get(c.name),
                                key_file,
                                cert_file,
                                dhparams_file): c for c in csps
            }

            for f in concurrent.futures.as_completed(futures_to_containers):
                container = futures_to_containers[f]
                try:
                    f.result()

                except Exception as e:
                    logging.error(f"[{container.name}] exception raised while configuring TLS")
                    logging.error(e)
                    rc = 1

        if rc != 0:
            raise RuntimeError('failed to configure TLS on some service')

        cscs = compose_project.containers(service_names=[
            context.irods_catalog_consumer_service()])

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures_to_containers = {
                executor.submit(configure_tls_on_server,
                                docker_client.containers.get(c.name),
                                key_file,
                                cert_file,
                                dhparams_file): c for c in cscs
            }

            for f in concurrent.futures.as_completed(futures_to_containers):
                container = futures_to_containers[f]
                try:
                    f.result()

                except Exception as e:
                    logging.error(f"[{container.name}] exception raised while configuring TLS")
                    logging.error(e)
                    rc = 1

        if rc != 0:
            raise RuntimeError('failed to configure TLS on some service')

    finally:
        os.unlink(key_file)
        os.unlink(cert_file)
        os.unlink(dhparams_file)
