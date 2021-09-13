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

    parser = argparse.ArgumentParser(description='Setup the iRODS catalog, catalog service provider, and catalog service consumers on a running docker-compose project.')
    parser.add_argument('--project-directory', metavar='PATH_TO_PROJECT_DIRECTORY', type=str, dest='project_directory',
                        help='Path to the docker-compose project on which packages will be installed.')
    parser.add_argument('--project-name', metavar='PROJECT_NAME', type=str, dest='project_name',
                        help='Name of the docker-compose project on which to install packages.')
    parser.add_argument('--os-platform-image', '-p', metavar='OS_PLATFORM_IMAGE_REPO_AND_TAG', dest='platform', type=str,
                        help='The repo:tag of the OS platform image to use')
    parser.add_argument('--database-image', '-d', metavar='DATABASE_IMAGE_REPO_AND_TAG', dest='database', type=str,
                        help='The repo:tag of the database image to use')
    parser.add_argument('--catalog-service-instance', metavar='CATALOG_SERVICE_INSTANCE_NUM', dest='catalog_instance', type=int, default=1,
                        help='The service instance number of the database server hosting the iRODS catalog.')
    parser.add_argument('--irods-catalog-provider-service-instance', metavar='IRODS_CATALOG_PROVIDER_INSTANCE_NUM', dest='irods_csp_instance', type=int, default=1,
                        help='The service instance number of the iRODS catalog service provider to set up.')
    parser.add_argument('--irods-catalog-consumer-service-instances', metavar='IRODS_CATALOG_CONSUMER_INSTANCE_NUM', dest='irods_csc_instances', type=int, nargs='+',
                        help='The service instance numbers of the iRODS catalog service consumers to set up.')
    parser.add_argument('--exclude-catalog-setup', dest='setup_catalog', action='store_false',
                        help='If indicated, skips the setup of iRODS tables and postgres user in the database.')
    parser.add_argument('--exclude-irods-catalog-provider-setup', dest='setup_csp', action='store_false',
                        help='If indicated, skips running the iRODS setup script on the catalog service provider.')
    parser.add_argument('--exclude-irods-catalog-consumers-setup', dest='setup_cscs', action='store_false',
                        help='If indicated, skips running the iRODS setup script on the catalog service consumers.')
    parser.add_argument('--odbc-driver-path', metavar='PATH_TO_ODBC_DRIVER_ARCHIVE', dest='odbc_driver', type=str,
                        help='Path to the ODBC driver archive file on the local machine. If not provided, the driver will be downloaded.')
    parser.add_argument('--force-recreate', dest='force_recreate', action='store_true',
                        help='If indicated, forces recreating the iRODS catalog and database user by dropping existing database and deleting existing user. NOTE: Setup must be run again to use iRODS.')
    parser.add_argument('--verbose', '-v', dest='verbosity', action='count', default=1,
                        help='Increase the level of output to stdout. CRITICAL and ERROR messages will always be printed.')

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

    project_name = args.project_name if args.project_name else compose_project.name

    platform = args.platform
    if not platform:
        platform = context.image_repo_and_tag_string(
            context.platform_image_repo_and_tag(project_name)
        )

        logging.debug('derived os platform image tag [{}]'.format(platform))

    database = args.database
    if not database:
        database = context.image_repo_and_tag_string(
            context.database_image_repo_and_tag(project_name))

        logging.debug('derived database image tag [{}]'.format(database))

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

