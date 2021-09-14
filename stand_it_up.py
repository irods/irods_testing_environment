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

    parser = argparse.ArgumentParser(description='Run iRODS tests in a consistent environment.')
    parser.add_argument('--project-directory', metavar='PATH_TO_PROJECT_DIRECTORY', type=str, dest='project_directory', default='.',
                        help='Path to the docker-compose project on which packages will be installed.')
    parser.add_argument('--project-name', metavar='PROJECT_NAME', type=str, dest='project_name',
                        help='Name of the docker-compose project on which to install packages.')
    parser.add_argument('--os-platform-image', '-p', metavar='OS_PLATFORM_IMAGE_REPO_AND_TAG', dest='platform', type=str,
                        help='The repo:tag of the OS platform image to use')
    parser.add_argument('--database-image', '-d', metavar='DATABASE_IMAGE_REPO_AND_TAG', dest='database', type=str,
                        help='The repo:tag of the database image to use')
    parser.add_argument('--package-directory', metavar='PATH_TO_DIRECTORY_WITH_PACKAGES', type=str, dest='package_directory',
                        help='Path to local directory which contains iRODS packages to be installed')
    parser.add_argument('--package-version', metavar='PACKAGE_VERSION_TO_DOWNLOAD', type=str, dest='package_version',
                        help='Version of iRODS to download and install. If neither --package-version or --package-directory is specified, the latest available version is used.')
    parser.add_argument('--odbc-driver-path', metavar='PATH_TO_ODBC_DRIVER_ARCHIVE', dest='odbc_driver', type=str,
                        help='Path to the ODBC driver archive file on the local machine. If not provided, the driver will be downloaded.')
    parser.add_argument('--verbose', '-v', dest='verbosity', action='count', default=1,
                        help='Increase the level of output to stdout. CRITICAL and ERROR messages will always be printed.')

    args = parser.parse_args()

    if args.package_directory and args.package_version:
        print('--package-directory and --package-version are incompatible')
        exit(1)

    if not args.project_name and not (args.database and args.platform):
        print('One of the following sets of options is required:')
        print('    --database-tag and --platform-tag')
        print('    --project-name of the form (.*<platform_repo>-<platform_tag>-<database_repo>-<database_tag>)')
        exit(1)

    compose_project = compose.cli.command.get_project(os.path.abspath(args.project_directory),
                                                      project_name=args.project_name)

    project_name = args.project_name if args.project_name else compose_project.name

    logs.configure(args.verbosity)

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

    # Install iRODS packages
    if args.package_directory:
        logging.warning('installing iRODS packages from directory [{}]'
                        .format(args.package_directory))

        install.install_local_irods_packages(docker_client,
                                             context.image_repo(platform),
                                             context.image_repo(database),
                                             args.package_directory,
                                             containers)
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
