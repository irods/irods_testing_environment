# grown-up modules
import logging
import os

# local modules
from irods_testing_environment.ssl_setup import configure_ssl_in_zone
from irods_testing_environment import logs

if __name__ == "__main__":
    import argparse
    import compose.cli.command
    import docker

    import cli

    parser = argparse.ArgumentParser(
        description="Configure SSL in a running iRODS Zone."
    )

    cli.add_common_args(parser)
    cli.add_compose_args(parser)

    args = parser.parse_args()

    docker_client = docker.from_env()

    compose_project = compose.cli.command.get_project(
        os.path.abspath(args.project_directory), project_name=args.project_name
    )

    logs.configure(args.verbosity)

    try:
        configure_ssl_in_zone(docker_client, compose_project)

    except Exception as e:
        logging.critical(e)
        exit(1)
