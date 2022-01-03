# grown-up modules
import json
import logging
import os

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dh, rsa
from cryptography.x509.oid import NameOID

# local modules
import context
import execute
import json_utils

def generate_ssl_certificate_key(directory=None):
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


def generate_ssl_self_signed_certificate(key, directory=None):
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


def generate_ssl_dh_params(generator=2, key_size=1024, directory=None):
    logging.info('generating dh params')

    parameters = dh.generate_parameters(generator=2, key_size=key_size)

    dhfile = os.path.join((directory or os.getcwd()), 'dhparams.pem')

    logging.info('writing dhparams to file [{}]'.format(dhfile))

    with open(dhfile, 'wb') as f:
        f.write(parameters.parameter_bytes(encoding=serialization.Encoding.PEM,
                                           format=serialization.ParameterFormat.PKCS3))

    return dhfile


def configure_ssl_on_server(container,
                            path_to_key_file_on_host,
                            path_to_cert_file_on_host,
                            path_to_dhparams_file_on_host):
    """Copy SSL files to the container and configure SSL on the iRODS server.

    Arguments:
    container -- the docker.Container on which SSL will be configured
    path_to_key_file_on_host -- path to file on host containing the private key for the cert
    path_to_cert_file_on_host -- path to file on host containing the self-signed cert
    path_to_dhparams_file_on_host -- path to file on host containing the dhparams PEM file
    """
    import archive

    key_file = os.path.join(context.irods_config(), 'server.key')
    dhparams_file = os.path.join(context.irods_config(), 'dhparams.pem')
    chain_file = os.path.join(context.irods_config(), 'chain.pem')
    cert_file = os.path.join(context.irods_config(), 'server.crt')

    logging.warning('configuring SSL [{}]'.format(container.name))

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

    # restart the server
    irodsctl = os.path.join(context.irods_home(), 'irodsctl')
    if execute.execute_command(container, '{} restart'.format(irodsctl), user='irods') is not 0:
        raise RuntimeError(
            'failed to restart iRODS server after SSL configuration [{}]'
            .format(container.name))

    logging.warning('SSL configured successfully [{}]'.format(container.name))


def configure_ssl_in_zone(docker_client, compose_project):
    import concurrent.futures
    import tempfile

    # Each irods_environment.json file is describing the cert this client will use and why
    # they think it is good. The testing environment is using a self-signed certificate, so
    # the certificate, key, and dhparams should be generated ONCE and copied to each server.
    #ssl_files_dir = tempfile.mkdtemp()
    key, key_file = generate_ssl_certificate_key()
    cert_file = generate_ssl_self_signed_certificate(key)
    dhparams_file = generate_ssl_dh_params()

    try:
        # Configure SSL on the catalog service provider first because communication with the
        # catalog service consumers depends on being able to communicate with the catalog
        # service provider. If SSL is not configured first on the catalog service provider
        # the catalog service consumers will not be able to communicate with it.
        configure_ssl_on_server(
            docker_client.containers.get(
                context.irods_catalog_provider_container(compose_project.name)
            ),
            key_file, cert_file, dhparams_file)

        containers = compose_project.containers(service_names=[
            context.irods_catalog_consumer_service()])

        rc = 0
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures_to_containers = {
                executor.submit(configure_ssl_on_server,
                                docker_client.containers.get(c.name),
                                key_file,
                                cert_file,
                                dhparams_file): c for c in containers
            }

            for f in concurrent.futures.as_completed(futures_to_containers):
                container = futures_to_containers[f]
                try:
                    f.result()

                except Exception as e:
                    logging.error('exception raised while configuring SSL [{}]'
                                  .format(container.name))
                    logging.error(e)
                    rc = 1

        if rc is not 0:
            raise RuntimeError('failed to configure SSL on some service')

    finally:
        os.unlink(key_file)
        os.unlink(cert_file)
        os.unlink(dhparams_file)
