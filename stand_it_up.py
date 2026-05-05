import logging
import os

import docker

import compose.cli.command
from irods_testing_environment import context, irods_config, services, tls_setup

if __name__ == "__main__":
    import argparse
    import textwrap

    import cli
    from irods_testing_environment import logs

    parser = argparse.ArgumentParser(description='Stand up an iRODS zone.')

    cli.add_common_args(parser)
    cli.add_compose_args(parser)
    cli.add_irods_package_args(parser)
    cli.add_irods_setup_args(parser)

    parser.add_argument('--consumer-instance-count',
                        metavar='IRODS_CATALOG_SERVICE_CONSUMER_INSTANCE_COUNT',
                        dest='consumer_count', type=int, default=0,
                        help=textwrap.dedent('''\
                            Number of iRODS Catalog Service Consumer service instances.'''))

    parser.add_argument('--use-unattended-install',
                        action='store_true', dest='do_unattended_install',
                        help='''\
                            If indicated, the iRODS servers will be set up using \
                            unattended installation.''')

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

    logs.configure(args.verbosity)

    logging.debug(f'environment variables:[{os.environ}]')

    # Bring up the services
    logging.debug('bringing up project [{}]'.format(ctx.compose_project.name))
    services.create_topology(
        ctx,
        externals_directory=args.irods_externals_package_directory,
        package_directory=args.package_directory,
        package_version=args.package_version,
        odbc_driver=args.odbc_driver,
        consumer_count=args.consumer_count,
        install_packages=args.install_packages,
        do_unattended_install=args.do_unattended_install,
        use_tls=args.use_tls,
    )

    containers = [
        ctx.docker_client.containers.get(
            context.container_name(ctx.compose_project.name, context.irods_catalog_provider_service())
        )
    ]

    # TLS configuration happens in setup as of 5.1.0, so only do this for prior versions when requested.
    if args.use_tls and irods_config.get_irods_version(containers[0]) < (5, 0, 90):
        tls_setup.configure_tls_in_zone(ctx.docker_client, ctx.compose_project)
