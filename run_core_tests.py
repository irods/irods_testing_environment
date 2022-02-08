# grown-up modules
import compose.cli.command
import docker
import logging
import os

# local modules
from irods_testing_environment import context
from irods_testing_environment import irods_config
from irods_testing_environment import ssl
from irods_testing_environment import services
from irods_testing_environment import test_utils

if __name__ == "__main__":
    import argparse
    import textwrap
    import time

    import cli
    from irods_testing_environment import logs

    parser = argparse.ArgumentParser(description='Run iRODS tests in a consistent environment.')

    cli.add_common_args(parser)
    cli.add_compose_args(parser)
    cli.add_database_config_args(parser)
    cli.add_irods_package_args(parser)
    cli.add_irods_test_args(parser)

    parser.add_argument('--concurrent-test-executor-count',
                        dest='executor_count', type=int, default=1,
                        help=textwrap.dedent('''\
                            Number of concurrent exeecutors to run tests at the same time.'''))

    parser.add_argument('--use-ssl',
                        dest='use_ssl', action='store_true',
                        help=textwrap.dedent('''\
                            Indicates that SSL should be configured and enabled in the test \
                            Zone.'''))

    args = parser.parse_args()

    if args.package_directory and args.package_version:
        print('--package-directory and --package-version are incompatible')
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

    job_name = test_utils.job_name(ctx.compose_project.name, args.job_name)

    output_directory = test_utils.make_output_directory(dirname, job_name)

    logs.configure(args.verbosity, os.path.join(output_directory, 'script_output.log'))

    rc = 0
    last_command_to_fail = None

    try:
        # Bring up the services
        logging.debug('bringing up project [{}]'.format(ctx.compose_project.name))
        consumer_count = 0
        services.create_topologies(ctx,
                                   zone_count=args.executor_count,
                                   externals_directory=args.irods_externals_package_directory,
                                   package_directory=args.package_directory,
                                   package_version=args.package_version,
                                   odbc_driver=args.odbc_driver,
                                   consumer_count=consumer_count)

        # Configure the containers for running iRODS automated tests
        logging.info('configuring iRODS containers for testing')
        irods_config.configure_irods_testing(ctx.docker_client, ctx.compose_project)

        # Get the container on which the command is to be executed
        containers = [
            ctx.docker_client.containers.get(
                context.container_name(ctx.compose_project.name,
                                       context.irods_catalog_provider_service(),
                                       service_instance=i + 1)
                )
            for i in range(args.executor_count)
        ]
        logging.debug('got containers to run on [{}]'.format(container.name for container in containers))

        options = list()

        if args.use_ssl:
            ssl.configure_ssl_in_zone(ctx.docker_client, ctx.compose_project)
            options.append('--use_ssl')

        if args.tests:
            tests = list(args.tests)

        else:
            tests = list(test_utils.get_test_list(containers[0]))


        start_time = time.time()

        rc = test_utils.run_specific_tests(containers, tests, options, args.fail_fast)

        end_time = time.time()

        logging.error('tests completed; time [{}] seconds, success [{}]'.format(end_time - start_time, rc is 0))

    except Exception as e:
        logging.critical(e)

        raise

    finally:
        logging.warning('collecting logs [{}]'.format(output_directory))
        logs.collect_logs(ctx.docker_client, ctx.irods_containers(), output_directory)

        ctx.compose_project.down(include_volumes=True, remove_image_type=False)

    exit(rc)
