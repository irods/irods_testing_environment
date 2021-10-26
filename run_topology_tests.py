# grown-up modules
import compose.cli.command
import docker
import logging
import os

# local modules
import context
import execute
import install
import irods_config
import irods_setup
import ssl
import test_utils

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
    cli.add_irods_test_args(parser)

    parser.add_argument('run_on',
                        metavar='<provider|consumer>',
                        choices=['provider', 'consumer'],
                        help=textwrap.dedent('''\
                            Indicates whether to run tests from provider or from consumer.\
                            '''))

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
    containers = list()

    try:
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

        run_on_consumer = args.run_on == 'consumer'

        target_service_name = context.irods_catalog_consumer_service() if run_on_consumer \
                              else context.irods_catalog_provider_service()

        # Get the container on which the command is to be executed
        container = ctx.docker_client.containers.get(
            context.container_name(ctx.compose_project.name,
                                   target_service_name,
                                   service_instance=1)
        )
        logging.debug('got container to run on [{}]'.format(container.name))

        options = list()

        options.append('--topology={}'.format('resource' if run_on_consumer else 'icat'))

        hostname_map = context.topology_hostnames(ctx.docker_client, ctx.compose_project)

        icat_hostname = hostname_map[context.container_name(ctx.compose_project.name,
                                     context.irods_catalog_provider_service())]
        hostname_1 = hostname_map[context.container_name(ctx.compose_project.name,
                                  context.irods_catalog_consumer_service(), 1)]
        hostname_2 = hostname_map[context.container_name(ctx.compose_project.name,
                                  context.irods_catalog_consumer_service(), 2)]
        hostname_3 = hostname_map[context.container_name(ctx.compose_project.name,
                                  context.irods_catalog_consumer_service(), 3)]

        options.extend(['--hostnames', icat_hostname, hostname_1, hostname_2, hostname_3])

        if args.use_ssl:
            ssl.configure_ssl_in_zone(ctx.docker_client, ctx.compose_project)
            options.append('--use_ssl')

        if args.tests:
            rc = test_utils.run_specific_tests(container,
                                               list(args.tests),
                                               options,
                                               args.fail_fast)

        else:
            rc = test_utils.run_python_test_suite(container, options)

    except Exception as e:
        logging.critical(e)

        raise

    finally:
        logging.warning('collecting logs [{}]'.format(output_directory))
        logs.collect_logs(ctx.docker_client, ctx.irods_containers(), output_directory)

        ctx.compose_project.down(include_volumes=True, remove_image_type=False)

    exit(rc)
