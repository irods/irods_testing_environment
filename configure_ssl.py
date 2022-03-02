# grown-up modules
import json
import logging
import os

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dh, rsa
from cryptography.x509.oid import NameOID

# local modules
from irods_testing_environment.ssl_setup import configure_ssl_in_zone
from irods_testing_environment import logs
from irods_testing_environment import context
from irods_testing_environment import execute
from irods_testing_environment import json_utils

if __name__ == "__main__":
    import argparse
    import compose.cli.command
    import docker

    import cli

    parser = argparse.ArgumentParser(description='Configure SSL in a running iRODS Zone.')

    cli.add_common_args(parser)
    cli.add_compose_args(parser)

    args = parser.parse_args()

    docker_client = docker.from_env()

    compose_project = compose.cli.command.get_project(os.path.abspath(args.project_directory),
                                                      project_name=args.project_name)

    logs.configure(args.verbosity)

    try:
        configure_ssl_in_zone(docker_client, compose_project)

    except Exception as e:
        logging.critical(e)
        exit(1)
