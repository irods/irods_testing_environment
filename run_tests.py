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
    import textwrap

    import cli

    parser = argparse.ArgumentParser(description='Run iRODS tests in a consistent environment.')

    cli.add_common_args(parser)
    cli.add_compose_args(parser)
    cli.add_database_config_args(parser)
    cli.add_irods_package_args(parser)

    parser.add_argument('--tests',
                        metavar='TESTS',
                        nargs='+',
                        help=textwrap.dedent('''\
                            Space-delimited list of tests to be run. If not provided, \
                            ALL tests will be run (--run_python-suite).'''))

    parser.add_argument('--output-directory', '-o',
                        metavar='FULLPATH_TO_DIRECTORY_FOR_OUTPUT',
                        dest='output_directory',
                        help='Full path to local directory for output from execution.')

    parser.add_argument('--job-name', '-j',
                        metavar='JOB_NAME',
                        dest='job_name',
                        help='Name of the test run')

    parser.add_argument('--fail-fast',
                        dest='fail_fast', action='store_true',
                        help=textwrap.dedent('''\
                            If indicated, exits on the first test that returns a non-zero exit \
                            code.'''))

    parser.add_argument('--topology',
                        metavar='<provider|consumer>',
                        choices=['provider', 'consumer'], dest='topology',
                        help=textwrap.dedent('''\
                            Indicates that the tests should be run in the context of a \
                            topology with option to run tests "from provider" or "from \
                            consumer".'''))

    args = parser.parse_args()

    if args.package_directory and args.package_version:
        print('--package-directory and --package-version are incompatible')
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

        platform, database = cli.platform_and_database(docker_client, compose_project)

        if args.irods_externals_package_directory:
            install.install_packages(docker_client,
                                     context.image_repo(platform),
                                     os.path.abspath(args.irods_externals_package_directory),
                                     containers,
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

        # Configure the containers for running iRODS automated tests
        logging.info('configuring iRODS containers for testing')
        irods_test_config.configure_irods_testing(docker_client, compose_project)

        run_on_consumer = args.topology and args.topology == 'consumer'

        target_service = context.irods_catalog_consumer_service() if run_on_consumer \
                         else context.irods_catalog_provider_service()

        # Get the container on which the command is to be executed
        container = docker_client.containers.get(
            context.container_name(compose_project.name, target_service)
        )
        logging.debug('got container to run on [{}]'.format(container.name))

        # start constructing the run_tests command
        command = ['python', 'scripts/run_tests.py']

        if args.topology:
            command.append('--topology={}'.format('resource' if run_on_consumer else 'icat'))

            hostname_map = context.topology_hostnames(docker_client, compose_project)

            icat_hostname = hostname_map[context.container_name(compose_project.name,
                                         'irods-catalog-provider')]
            hostname_1 = hostname_map[context.container_name(compose_project.name,
                                      'irods-catalog-consumer', 1)]
            hostname_2 = hostname_map[context.container_name(compose_project.name,
                                      'irods-catalog-consumer', 2)]
            hostname_3 = hostname_map[context.container_name(compose_project.name,
                                      'irods-catalog-consumer', 3)]

            command.append('--hostnames {}'.format(' '.join([icat_hostname,
                                                             hostname_1,
                                                             hostname_2,
                                                             hostname_3])))

        # Serially execute the list of commands provided in the input
        if args.tests:
            for test in list(args.tests):
                cmd = command + ['--run_specific_test', test]
                ec = execute.execute_command(container,
                                             ' '.join(cmd),
                                             user='irods',
                                             workdir=context.irods_home(),
                                             stream_output=True)

                if ec is not 0:
                    rc = ec
                    last_command_to_fail = cmd
                    logging.warning('command exited with error code [{}] [{}] [{}]'
                                    .format(ec, cmd, container.name))

                    if args.fail_fast:
                        logging.critical('command failed [{}]'.format(cmd))
                        break

            if rc is not 0:
                logging.error('last command to fail [{}]'.format(last_command_to_fail))

        else:
            ec = execute.execute_command(container,
                                         ' '.join(command + ['--run_python_suite']),
                                         user='irods',
                                         workdir=context.irods_home(),
                                         stream_output=True)

            if ec is not 0:
                rc = ec
                last_command_to_fail = command
                logging.warning('command exited with error code [{}] [{}] [{}]'
                                .format(ec, command, container.name))

    except Exception as e:
        logging.critical(e)

        raise

    finally:
        logging.warning('collecting logs [{}]'.format(output_directory))
        logs.collect_logs(docker_client, containers, output_directory)

        compose_project.down(include_volumes=True, remove_image_type=False)

    exit(rc)
