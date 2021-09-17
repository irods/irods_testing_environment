# grown-up modules
import compose.cli.command
import docker
import logging
import os

# local modules
import context
import database_setup
import irods_setup

if __name__ == "__main__":
    import argparse
    import logs
    import textwrap

    import cli

    parser = argparse.ArgumentParser(description='Setup the iRODS catalog, catalog service provider, and catalog service consumers on a running docker-compose project.')

    cli.add_common_args(parser)
    cli.add_compose_args(parser)
    cli.add_database_config_args(parser)
    cli.add_platform_args(parser)

    parser.add_argument('--irods-zone-name',
                        metavar='ZONE_NAME',
                        dest='zone_name', default='tempZone',
                        help='Desired name for the iRODS Zone being set up.')

    parser.add_argument('--catalog-service-instance',
                        metavar='CATALOG_SERVICE_INSTANCE_NUM',
                        dest='catalog_instance', type=int, default=1,
                        help=textwrap.dedent('''\
                            The Compose service instance number of the database server \
                            hosting the iRODS catalog.'''))

    parser.add_argument('--irods-catalog-provider-service-instance',
                        metavar='IRODS_CATALOG_PROVIDER_INSTANCE_NUM',
                        dest='irods_csp_instance', type=int, default=1,
                        help=textwrap.dedent('''\
                            The Compose service instance number of the iRODS catalog service \
                            provider to set up.'''))

    parser.add_argument('--irods-catalog-consumer-service-instances',
                        metavar='IRODS_CATALOG_CONSUMER_INSTANCE_NUM',
                        dest='irods_csc_instances', type=int, nargs='+',
                        help=textwrap.dedent('''\
                            The Compose service instance numbers of the iRODS catalog service \
                            consumers to set up.'''))

    parser.add_argument('--exclude-catalog-setup',
                        dest='setup_catalog', action='store_false',
                        help='Skip setup of iRODS tables and user in the database.')

    parser.add_argument('--exclude-irods-catalog-provider-setup',
                        dest='setup_csp', action='store_false',
                        help='Skip iRODS setup script on the catalog service provider.')

    parser.add_argument('--exclude-irods-catalog-consumers-setup',
                        dest='setup_cscs', action='store_false',
                        help='Skip iRODS setup script on the catalog service consumers.')

    parser.add_argument('--force-recreate',
                        dest='force_recreate', action='store_true',
                        help=textwrap.dedent('''\
                            Force recreating the iRODS catalog and database user by \
                            dropping existing database and deleting existing user. \
                            NOTE: iRODS setup script must be run again to use iRODS.'''))

    args = parser.parse_args()

    logs.configure(args.verbosity)

    docker_client = docker.from_env()

    project_directory = args.project_directory or os.getcwd()

    compose_project = compose.cli.command.get_project(
        project_dir=os.path.abspath(project_directory),
        project_name=args.project_name)

    logging.debug('provided project name [{0}], docker-compose project name [{1}]'
                  .format(args.project_name, compose_project.name))

    if len(compose_project.containers()) is 0:
        logging.critical('no containers found for project [directory=[{0}], name=[{1}]]'
                         .format(os.path.abspath(project_directory),
                                 args.project_name))

        exit(1)

    project_name = args.project_name or compose_project.name

    platform, database = cli.platform_and_database(args.platform, args.database, project_name)

    try:
        if args.setup_catalog:
            database_setup.setup_catalog(docker_client,
                                         compose_project,
                                         database,
                                         service_instance=args.catalog_instance,
                                         force_recreate=args.force_recreate)

        if args.setup_csp:
            irods_setup.setup_irods_catalog_provider(docker_client,
                                                     compose_project,
                                                     platform,
                                                     database,
                                                     args.catalog_instance,
                                                     args.irods_csp_instance,
                                                     args.odbc_driver)

        if args.setup_cscs:
            irods_setup.setup_irods_catalog_consumers(docker_client,
                                                      compose_project,
                                                      platform,
                                                      database,
                                                      args.irods_csp_instance,
                                                      args.irods_csc_instances)

    except Exception as e:
        logging.critical(e)
        raise

