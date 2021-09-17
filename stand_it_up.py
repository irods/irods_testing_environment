# grown-up modules
import compose.cli.command
import docker
import logging
import os

# local modules
import context
import database_setup
import execute
import install
import irods_setup
import irods_test_config

if __name__ == "__main__":
    import argparse
    import logs

    import cli

    parser = argparse.ArgumentParser(description='Stand up an iRODS zone.')

    cli.add_common_args(parser)
    cli.add_compose_args(parser)
    cli.add_database_config_args(parser)
    cli.add_irods_package_args(parser)

    args = parser.parse_args()

    if args.package_directory and args.package_version:
        print('--package-directory and --package-version are incompatible')
        exit(1)

    compose_project = compose.cli.command.get_project(os.path.abspath(args.project_directory),
                                                      project_name=args.project_name)

    logs.configure(args.verbosity)

    project_name = args.project_name or compose_project.name

    rc = 0
    last_command_to_fail = None
    containers = list()
    docker_client = docker.from_env()

    # Bring up the services
    logging.debug('bringing up project [{}]'.format(compose_project.name))
    consumer_count = 3
    containers = compose_project.up(scale_override={
        context.irods_catalog_consumer_service(): consumer_count
    })

    platform, database = cli.platform_and_database(docker_client, compose_project)

    if args.irods_externals_package_directory:
        install.install_packages(docker_client,
                                 context.image_repo(platform),
                                 os.path.abspath(args.irods_externals_package_directory),
                                 target_containers,
                                 context.irods_externals_package_names())

    # Install iRODS packages
    if args.package_directory:
        logging.warning('installing iRODS packages from directory [{}]'
                        .format(args.package_directory))

        install.install_packages(docker_client,
                                 context.image_repo(platform),
                                 os.path.abspath(args.package_directory),
                                 containers,
                                 context.irods_package_names(context.image_repo(database)))

    else:
        # Even if no version was provided, we default to using the latest official release
        logging.warning('installing official iRODS packages [{}]'
                        .format(args.package_version))

        install.install_official_irods_packages(docker_client,
                                                context.image_repo(platform),
                                                context.image_repo(database),
                                                args.package_version,
                                                containers)

    database_setup.setup_catalog(docker_client, compose_project, database)

    irods_setup.setup_irods_catalog_provider(docker_client,
                                             compose_project,
                                             platform,
                                             database,
                                             args.odbc_driver)

    irods_setup.setup_irods_catalog_consumers(docker_client,
                                              compose_project,
                                              platform,
                                              database)
