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

def job_name(project_name, prefix=None):
    """Construct unique job name based on the docker-compose project name.

    The job name returned will be of the form: `project_name`_`prefix`_`uuid.uuid4()`

    If no `prefix` is provided, the job name will be of the form: `project_name`_`uuid.uuid4()`

    Arguments:
    project_name -- docker-compose project name which identifies the type of test being run
    prefix -- optional prefix for the job name
    """
    import uuid
    # TODO: use timestamps, also
    if prefix:
        return '_'.join([prefix, project_name, str(uuid.uuid4())])

    return '_'.join([project_name, str(uuid.uuid4())])


def make_output_directory(dirname, basename):
    """Create a directory for job output and return its full path.

    Arguments:
    dirname -- base directory in which the unique subdirectory for output will be created
    basename -- unique subdirectory which will be created under the provided dirname
    """
    directory = os.path.join(os.path.abspath(dirname), basename)

    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST or not os.path.isdir(directory):
            raise

    return directory


if __name__ == "__main__":
    import argparse
    import logs

    parser = argparse.ArgumentParser(description='Run iRODS tests in a consistent environment.')
    parser.add_argument('commands', metavar='COMMANDS', nargs='+',
                        help='Space-delimited list of commands to be run')
    parser.add_argument('--output-directory', '-o', metavar='FULLPATH_TO_DIRECTORY_FOR_OUTPUT', dest='output_directory', type=str,
                        help='Full path to local directory for output from execution.')
    parser.add_argument('--job-name', '-j', metavar='JOB_NAME', dest='job_name', type=str,
                        help='Name of the test run')
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
    parser.add_argument('--target-service-instance', '-t', metavar='TARGET_SERVICE_INSTANCE', dest='target_service_instance', type=str, nargs=2, default='irods-catalog-provider 1',
                        help='The service instance on which the command will run represented as "SERVICE_NAME SERVICE_INSTANCE_NUM".')
    parser.add_argument('--fail-fast', dest='fail_fast', action='store_true',
                        help='If indicated, exits on the first command that returns a non-zero exit code.')
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

    if args.output_directory:
        dirname = args.output_directory
    else:
        import tempfile
        dirname = tempfile.mkdtemp(prefix=project_name)

    job_name = job_name(compose_project.name, args.job_name)

    output_directory = make_output_directory(dirname, job_name)

    logs.configure(args.verbosity, os.path.join(output_directory, 'script_output.log'))

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

    try:
        # Bring up the services
        logging.debug('bringing up project [{}]'.format(compose_project.name))
        consumer_count = 3
        containers = compose_project.up(scale_override={
            context.irods_catalog_consumer_service(): consumer_count
        })

        # TODO: install iRODS externals packages

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

        # Configure the containers for running iRODS automated tests
        logging.info('configuring iRODS containers for testing')
        irods_test_config.configure_irods_testing(docker_client, compose_project)

        # Get the container on which the command is to be executed
        logging.debug('--target-service-instance [{}]'.format(args.target_service_instance.split()))
        target_service_name, target_service_instance = args.target_service_instance.split()

        container = docker_client.containers.get(
            context.container_name(compose_project.name,
                                   target_service_name,
                                   target_service_instance)
        )
        logging.debug('got container to run on [{}]'.format(container.name))

        # Serially execute the list of commands provided in the input
        for command in list(args.commands):
            ec = execute.execute_command(container,
                                         command,
                                         user='irods',
                                         workdir=context.irods_home(),
                                         stream_output=True)

            if ec is not 0:
                rc = ec
                last_command_to_fail = command
                logging.warning('command exited with error code [{}] [{}] [{}]'
                              .format(ec, command, container.name))

                if args.fail_fast:
                    logging.critical('command failed [{}]'.format(command))
                    break

        if rc is not 0:
            logging.error('last command to fail [{}]'.format(last_command_to_fail))

    except Exception as e:
        logging.critical(e)

        raise

    finally:
        logging.warning('collecting logs [{}]'.format(output_directory))
        logs.collect_logs(docker_client, containers, output_directory)

        compose_project.down(include_volumes=True, remove_image_type=False)

    exit(rc)
