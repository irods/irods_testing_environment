# grown-up modules
import compose.cli.command
import docker
import logging
import os

# local modules
from . import context
from . import execute
from . import json_utils

def backup_file(container, file_path):
    backup_file_path = file_path + '.orig'
    if execute.execute_command(container, f"cp {file_path} {backup_file_path}") != 0:
        raise RuntimeError('failed to backup [{}] [{}]'.format(file_path, container.name))


def restore_file(container, file_path):
    backup_file_path = file_path + '.orig'
    if execute.execute_command(container, f"cp {backup_file_path} {file_path}") != 0:
        raise RuntimeError('failed to restore [{}] [{}]'.format(file_path, container.name))


def configure_tls_in_client(container, client_tls_negotiation, irods_env=None):
    env = irods_env or json_utils.get_json_from_file(container,
                                                     context.service_account_irods_env())

    env['irods_client_server_policy'] = client_tls_negotiation
    json_utils.put_json_to_file(container, context.service_account_irods_env(), env)


def configure_tls_in_server(container, server_tls_negotiation):
    acPreConnect = 'acPreConnect(*OUT) {{ *OUT=\\"{}\\"; }}'.format(server_tls_negotiation)

    add_acPreConnect = 'bash -c \'echo "{}" > {}; cat {} {} > {}\''.format(
        acPreConnect,
        context.core_re() + '.tmp',
        context.core_re() + '.tmp',
        context.core_re() + '.orig',
        context.core_re())

    if execute.execute_command(container, add_acPreConnect) != 0:
        raise RuntimeError('failed to update core.re [{}]'.format(container.name))


def show_configurations(container, stream_output=False):
    show_core_re = 'bash -c \'cat {} | head -n30\''.format(context.core_re())
    show_server_config = 'bash -c "cat {} | jq \'.\'"'.format(context.server_config())
    show_irods_env = 'bash -c "cat {} | jq \'.\'"'.format(context.service_account_irods_env())

    if execute.execute_command(container, show_core_re, stream_output=stream_output) != 0:
        raise RuntimeError('failed to cat core.re [{}]'.format(container.name))

    if execute.execute_command(container, show_server_config, stream_output=stream_output) != 0:
        raise RuntimeError('failed to cat server_config [{}]'.format(container.name))

    if execute.execute_command(container, show_irods_env, stream_output=stream_output) != 0:
        raise RuntimeError('failed to cat irods_environment [{}]'.format(container.name))


def configure_negotiation_key(container, negotiation_key, server_config=None):
    config = server_config or json_utils.get_json_from_file(container, context.server_config())

    if negotiation_key is not None:
        logging.info('adding "negotiation_key" [{}] to config'.format(negotiation_key))
        config['negotiation_key'] = negotiation_key
    elif 'negotiation_key' in config:
        logging.info('deleting "negotiation_key" from config')
        del config['negotiation_key']

    json_utils.put_json_to_file(container, context.server_config(), config)
