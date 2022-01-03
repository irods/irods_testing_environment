# grown-up modules
import compose.cli.command
import docker
import logging
import os

# local modules
import context
import execute
import json_utils

def backup_file(container, file_path):
    backup_file_path = file_path + '.orig'
    if execute.execute_command(container, 'cp {} {}'.format(file_path, backup_file_path)) is not 0:
        raise RuntimeError('failed to backup [{}] [{}]'.format(file_path, container.name))


def restore_file(container, file_path):
    backup_file_path = file_path + '.orig'
    if execute.execute_command(container, 'cp {} {}'.format(backup_file_path, file_path)) is not 0:
        raise RuntimeError('failed to restore [{}] [{}]'.format(file_path, container.name))


def do_negotiation_key_tests(target_container,
                             remote_container,
                             client_policies,
                             server_policies,
                             negotiation_keys,
                             remote_server_policy='CS_NEG_REQUIRE'):
    irods_env = json_utils.get_json_from_file(target_container, context.service_account_irods_env())
    server_config = json_utils.get_json_from_file(target_container, context.server_config())

    rc = 0

    configure_ssl_in_server(remote_container, remote_server_policy)
    #show_configurations(remote_container, True)

    for client_ssl_negotiation in client_policies:
        configure_ssl_in_client(target_container, client_ssl_negotiation, irods_env)

        for server_ssl_negotiation in server_policies:
            configure_ssl_in_server(target_container, server_ssl_negotiation)

            for nk in negotiation_keys:
                logging.warning(
                    'irods_client_server_policy [{}] acPreConnect [{}] negotiation_key [{}]'
                    .format(client_ssl_negotiation, server_ssl_negotiation, nk))

                configure_negotiation_key(target_container, nk, server_config)

                show_configurations(target_container)

                ec = execute.execute_command(target_container, 'ils', user='irods', stream_output=True)
                if ec is not 0:
                    logging.error('running "ils" resulted in an error [{}] [{}] [{}] [{}]'
                                  .format(ec, client_ssl_negotiation, server_ssl_negotiation, nk))
                    rc = ec
                else:
                    logging.warning('success!')

    return rc


def test_negotiation_key(target_container, remote_container):
    logging.info('target [{}] remote [{}]'.format(target_container.name, remote_container.name))

    execute.execute_command(target_container, 'apt install -y jq')
    execute.execute_command(remote_container, 'apt install -y jq')

    irods_client_server_policies = ['CS_NEG_DONT_CARE',
                                    'CS_NEG_REFUSE',
                                    'CS_NEG_REQUIRE']

    negotiation_keys = [None,                                       # missing
                        '',                                         # empty
                        'too_short',                                # too short
                        '32_byte_server_negotiation_key__too_long', # too long
                        '32_byte_server_negotiation_key__']         # valid

    backup_file(remote_container, context.service_account_irods_env())
    backup_file(remote_container, context.server_config())
    backup_file(remote_container, context.core_re())
    backup_file(target_container, context.service_account_irods_env())
    backup_file(target_container, context.server_config())
    backup_file(target_container, context.core_re())

    try:
        return do_negotiation_key_tests(target_container,
                                        remote_container,
                                        irods_client_server_policies,
                                        irods_client_server_policies,
                                        negotiation_keys)

    finally:
        restore_file(remote_container, context.service_account_irods_env())
        restore_file(remote_container, context.server_config())
        restore_file(remote_container, context.core_re())
        restore_file(target_container, context.service_account_irods_env())
        restore_file(target_container, context.server_config())
        restore_file(target_container, context.core_re())

    return 1


if __name__ == "__main__":
    import argparse

    import cli
    import logs

    parser = argparse.ArgumentParser(description='Run negotiation_key test.')

    cli.add_common_args(parser)
    cli.add_compose_args(parser)

    args = parser.parse_args()

    docker_client = docker.from_env()

    project_directory = os.path.abspath(args.project_directory or os.getcwd())

    compose_project = compose.cli.command.get_project(project_dir=project_directory,
                                                      project_name=args.project_name)

    logs.configure(args.verbosity)

    try:
        if True:
            exit(
                test_negotiation_key(
                    docker_client.containers.get(
                        context.irods_catalog_consumer_container(compose_project.name)
                    ),
                    docker_client.containers.get(
                        context.irods_catalog_provider_container(compose_project.name)
                    )
                )
            )
        else:
            exit(
                test_negotiation_key(
                    docker_client.containers.get(
                        context.irods_catalog_provider_container(compose_project.name)
                    ),
                    docker_client.containers.get(
                        context.irods_catalog_consumer_container(compose_project.name)
                    )
                )
            )

    except Exception as e:
        logging.critical(e)
        exit(1)
