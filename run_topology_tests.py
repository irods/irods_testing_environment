# grown-up modules
import compose.cli.command
import docker
import logging
import os

# local modules
from irods_testing_environment import archive
from irods_testing_environment import context
from irods_testing_environment import execute
from irods_testing_environment import install
from irods_testing_environment import irods_config
from irods_testing_environment import services
from irods_testing_environment import tls_setup
from irods_testing_environment import test_utils

if __name__ == "__main__":
    import argparse
    import textwrap

    from irods_testing_environment import logs
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

    parser.add_argument('--use-tls',
                        dest='use_tls', action='store_true',
                        help=textwrap.dedent('''\
                            Indicates that TLS should be configured and enabled in the test \
                            Zone.'''))

    args = parser.parse_args()

    if not args.package_version and not args.install_packages:
        print('--irods-package-version is required when using --use-static-image')
        exit(1)

    if args.package_directory and args.package_version:
        print('--irods-package-directory and --irods-package-version are incompatible')
        exit(1)

    project_directory = os.path.abspath(args.project_directory or os.getcwd())

    if not args.install_packages:
        os.environ['dockerfile'] = 'release.Dockerfile'
        if args.package_version:
            os.environ['irods_package_version'] = args.package_version

    ctx = context.context(docker.from_env(use_ssh_client=True),
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
    containers = None

    try:
        # some constants
        zone_name = 'tempZone'
        consumer_count = 3

        if args.do_setup:
            # Bring up the services
            logging.debug('bringing up project [{}]'.format(ctx.compose_project.name))
            services.create_topologies(ctx,
                                       zone_count=args.executor_count,
                                       externals_directory=args.irods_externals_package_directory,
                                       package_directory=args.package_directory,
                                       package_version=args.package_version,
                                       odbc_driver=args.odbc_driver,
                                       consumer_count=consumer_count,
                                       install_packages=args.install_packages,
                                       do_unattended_install=args.do_unattended_install)

            # Configure the containers for running iRODS automated tests
            logging.info('configuring iRODS containers for testing')
            irods_config.configure_irods_testing(ctx.docker_client, ctx.compose_project)

        run_on_consumer = args.run_on == 'consumer'

        if run_on_consumer:
            target_service_name = context.irods_catalog_consumer_service()
        else:
            target_service_name = context.irods_catalog_provider_service()

        # Get the containers on which the command is to be executed
        containers = list()
        for i in range(args.executor_count):
            if run_on_consumer:
                service_instance = i * consumer_count + 1
            else:
                service_instance = i + 1

            containers.append(
                ctx.docker_client.containers.get(
                    context.container_name(ctx.compose_project.name,
                                           target_service_name,
                                           service_instance=service_instance)
                    )
            )
        logging.debug('got containers to run on [{}]'.format(container.name for container in containers))

        options_base = ['--xml_output']
        options_base.append('--topology={}'.format('resource' if run_on_consumer else 'icat'))

        hostname_map = context.project_hostnames(ctx.docker_client, ctx.compose_project)

        if args.use_tls:
            options_base.append('--use_ssl')
            if args.do_setup:
                tls_setup.configure_tls_in_zone(ctx.docker_client, ctx.compose_project)

        options_list = list()
        for i in range(args.executor_count):
            logging.debug('hostname_map:{}'.format(hostname_map))
            hostnames_option = [
                '--hostnames',
                hostname_map[
                    # The service instance number is 1-based, so we need to add 1.
                    context.container_name(ctx.compose_project.name, context.irods_catalog_provider_service(), i + 1)
                ]
            ]

            consumer_hostname_map = {}
            for c in ctx.compose_project.containers():
                container_service_instance = context.service_instance(c.name)
                # The range of service instances for the catalog service consumers for a given zone will be a
                # consecutive range of size consumer_count starting with 1.
                consumer_service_instances_for_this_zone = range(i * consumer_count + 1, (i + 1) * consumer_count + 1)
                logging.debug('consumer_service_instances_for_this_zone:[{}]'.format([inst for inst in consumer_service_instances_for_this_zone]))
                container_is_consumer_for_this_zone = \
                    context.is_irods_catalog_consumer_container(c) and \
                    container_service_instance in consumer_service_instances_for_this_zone
                if container_is_consumer_for_this_zone:
                    consumer_hostname_map[c.name] = hostname_map[
                        context.container_name(
                            ctx.compose_project.name,
                            context.irods_catalog_consumer_service(),
                            context.service_instance(c.name)
                            )
                        ]

            # The hostnames cannot be indiscriminately inserted into the hostnames_option because the consumer
            # containers will not necessarily be in order. Therefore, a map of the container names to hostnames is
            # built up and sorted by keys to ensure that the hostnames provided to run_tests.py is in order.
            hostnames_option.extend([consumer_hostname_map[k] for k in sorted(consumer_hostname_map)])

            options_list.append(options_base + hostnames_option)

        logging.info(options_list)

        rc = test_utils.run_specific_tests(containers, args.tests, options_list, args.fail_fast)

    except Exception as e:
        logging.critical(e)

        raise

    finally:
        if containers:
            # Just grab the version and sha from the first container since they are all running the same thing.
            cli.log_irods_version_and_commit_id(containers[0])

        if args.save_logs:
            try:
                logging.error('collecting logs [{}]'.format(output_directory))

                # collect the usual logs
                logs.collect_logs(ctx.docker_client, ctx.irods_containers(), output_directory)

                # and then the test reports
                archive.collect_files_from_containers(ctx.docker_client,
                                                      containers,
                                                      [os.path.join(context.irods_home(), 'test-reports')],
                                                      output_directory)

            except Exception as e:
                logging.error(e)
                logging.error('failed to collect some log files')

                if rc == 0:
                    rc = 1


        if args.cleanup_containers:
            ctx.compose_project.down(include_volumes=True, remove_image_type=False)

    exit(rc)
