# grown-up modules
import compose.cli.command
import docker
import logging
import os

# local modules
import context
import database_setup
import execute
import federate
import install
import irods_setup
import irods_config

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

    parser.add_argument('--use-federation',
                        dest='use_federation', action='store_true',
                        help=textwrap.dedent('''\
                            Indicates that the federation test suite should be run and so the \
                            appropriate Zones should be created and configured for testing.'''))

    args = parser.parse_args()

    if args.package_directory and args.package_version:
        print('--package-directory and --package-version are incompatible')
        exit(1)

    if args.topology and args.use_federation:
        print('--topology and --use-federation are incompatible')
        exit(1)

    project_directory = os.path.abspath(args.project_directory or os.getcwd())

    ctx = context.context(docker.from_env(),
                          compose.cli.command.get_project(
                              project_dir=project_directory,
                              project_name=args.project_name))

    if args.output_directory:
        dirname = args.output_directory
    else:
        import tempfile
        dirname = tempfile.mkdtemp(prefix=ctx.compose_project.name)

    job_name = job_name(ctx.compose_project.name, args.job_name)

    output_directory = make_output_directory(dirname, job_name)

    logs.configure(args.verbosity, os.path.join(output_directory, 'script_output.log'))

    rc = 0
    last_command_to_fail = None
    containers = list()

    try:
        if args.use_federation:
            # Bring up the services
            logging.debug('bringing up project [{}]'.format(ctx.compose_project.name))
            containers = ctx.compose_project.up(scale_override={
                context.irods_catalog_database_service(): 2,
                context.irods_catalog_provider_service(): 2,
                context.irods_catalog_consumer_service(): 0
            })

            # The catalog consumers are only determined after the containers are running
            zone_info_list = federate.get_info_for_zones(ctx, ['tempZone', 'otherZone'])

            install.install_irods_packages(ctx,
                                           externals_directory=args.irods_externals_package_directory,
                                           package_directory=args.package_directory,
                                           package_version=args.package_version)

            for z in zone_info_list:
                irods_setup.setup_irods_zone(ctx,
                                             provider_service_instance=z.provider_service_instance,
                                             database_service_instance=z.database_service_instance,
                                             consumer_service_instances=z.consumer_service_instances,
                                             odbc_driver=args.odbc_driver,
                                             zone_name=z.zone_name,
                                             zone_key=z.zone_key,
                                             negotiation_key=z.negotiation_key)

            federate.form_federation_clique(ctx, zone_info_list)

        else:
            # Bring up the services
            logging.debug('bringing up project [{}]'.format(ctx.compose_project.name))
            consumer_count = 3
            containers = ctx.compose_project.up(scale_override={
                context.irods_catalog_consumer_service(): consumer_count
            })

            install.install_irods_packages(ctx,
                                           externals_directory=args.irods_externals_package_directory,
                                           package_directory=args.package_directory,
                                           package_version=args.package_version)

            irods_setup.setup_irods_zone(ctx, odbc_driver=args.odbc_driver)

        # Configure the containers for running iRODS automated tests
        logging.info('configuring iRODS containers for testing')
        irods_config.configure_irods_testing(ctx.docker_client, ctx.compose_project)

        run_on_consumer = args.topology and args.topology == 'consumer'

        target_service_name = context.irods_catalog_consumer_service() if run_on_consumer \
                              else context.irods_catalog_provider_service()

        target_service_instance = 2 if args.use_federation else 1

        # Get the container on which the command is to be executed
        container = ctx.docker_client.containers.get(
            context.container_name(ctx.compose_project.name,
                                   target_service_name,
                                   target_service_instance)
        )
        logging.debug('got container to run on [{}]'.format(container.name))

        # start constructing the run_tests command
        command = ['python', 'scripts/run_tests.py']

        if args.topology:
            command.append('--topology={}'.format('resource' if run_on_consumer else 'icat'))

            hostname_map = context.topology_hostnames(ctx.docker_client, ctx.compose_project)

            icat_hostname = hostname_map[context.container_name(ctx.compose_project.name,
                                         'irods-catalog-provider')]
            hostname_1 = hostname_map[context.container_name(ctx.compose_project.name,
                                      'irods-catalog-consumer', 1)]
            hostname_2 = hostname_map[context.container_name(ctx.compose_project.name,
                                      'irods-catalog-consumer', 2)]
            hostname_3 = hostname_map[context.container_name(ctx.compose_project.name,
                                      'irods-catalog-consumer', 3)]

            command.extend(['--hostnames', icat_hostname, hostname_1, hostname_2, hostname_3])

        if args.use_federation:
            remote_container = ctx.docker_client.containers.get(
                context.container_name(ctx.compose_project.name,
                                       context.irods_catalog_provider_service()))

            version = irods_config.get_json_from_file(remote_container, '/var/lib/irods/VERSION.json')['irods_version']
            zone = irods_config.get_json_from_file(remote_container, context.server_config())['zone_name']
            host = context.topology_hostnames(ctx.docker_client, ctx.compose_project)[
                    context.irods_catalog_provider_container(ctx.compose_project.name)]

            command.extend(['--federation', version, zone, host,
                            '--run_specific_test', 'test_federation'])

            # configure federation for testing
            irods_config.configure_irods_federation_testing(ctx, zone_info_list[0], zone_info_list[1])

            execute.execute_command(container, 'iadmin lu', user='irods')
            execute.execute_command(container, 'iadmin lz', user='irods')
            logging.warning('executing command [{}] [{}]'.format(command, container.name))

            ec = execute.execute_command(container,
                                         ' '.join(command),
                                         user='irods',
                                         workdir=context.irods_home(),
                                         stream_output=True)

            if ec is not 0:
                rc = ec
                last_command_to_fail = command
                logging.warning('command exited with error code [{}] [{}] [{}]'
                                .format(ec, command, container.name))

        elif args.tests:
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
        logs.collect_logs(ctx.docker_client, ctx.irods_containers(), output_directory)

        ctx.compose_project.down(include_volumes=True, remove_image_type=False)

    exit(rc)
