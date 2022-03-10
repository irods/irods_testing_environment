# grown-up modules
import compose.cli.command
import docker
import logging
import os

# local modules
import context
import execute
import federate
import install
import irods_config
import irods_setup
#import ssl_setup
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

    #parser.add_argument('--use-ssl',
                        #dest='use_ssl', action='store_true',
                        #help=textwrap.dedent('''\
                            #Indicates that SSL should be configured and enabled in the test \
                            #Zone.'''))

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
        if args.do_setup:
            # Bring up the services
            logging.debug('bringing up project [{}]'.format(ctx.compose_project.name))
            ctx.compose_project.build()
            containers = ctx.compose_project.up(scale_override={
                context.irods_catalog_database_service(): 2,
                context.irods_catalog_provider_service(): 2,
                context.irods_catalog_consumer_service(): 0
            })

        # The catalog consumers are only determined after the containers are running
        zone_info_list = federate.get_info_for_zones(ctx, ['tempZone', 'otherZone'])

        if args.do_setup:
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

            # Configure the containers for running iRODS automated tests
            logging.info('configuring iRODS containers for testing')
            irods_config.configure_irods_testing(ctx.docker_client, ctx.compose_project)

        # Get the container on which the command is to be executed
        container = ctx.docker_client.containers.get(
            context.container_name(ctx.compose_project.name,
                                   context.irods_catalog_provider_service(),
                                   service_instance=2)
        )
        logging.debug('got container to run on [{}]'.format(container.name))

        options = list()

        #if args.do_setup and args.use_ssl:
            #ssl_setup.configure_ssl_in_zone(ctx.docker_client, ctx.compose_project)
            #options.append('--use_ssl')

        remote_container = ctx.docker_client.containers.get(
            context.container_name(ctx.compose_project.name,
                                   context.irods_catalog_provider_service()))

        version = irods_config.get_irods_version(remote_container)
        zone = irods_config.get_irods_zone_name(remote_container)
        host = context.topology_hostnames(ctx.docker_client, ctx.compose_project)[
                context.irods_catalog_provider_container(ctx.compose_project.name)]

        options.extend(['--federation', version, zone, host])

        # configure federation for testing
        irods_config.configure_irods_federation_testing(ctx, zone_info_list[0], zone_info_list[1])

        execute.execute_command(container, 'iadmin lu', user='irods')
        execute.execute_command(container, 'iadmin lz', user='irods')

        rc = test_utils.run_specific_tests([container],
                                           args.tests or ['test_federation'],
                                           options,
                                           args.fail_fast)

    except Exception as e:
        logging.critical(e)

        raise

    finally:
        logging.warning('collecting logs [{}]'.format(output_directory))
        logs.collect_logs(ctx.docker_client, ctx.irods_containers(), output_directory)

        ctx.compose_project.down(include_volumes=True, remove_image_type=False)

    exit(rc)
