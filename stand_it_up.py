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
import services
import ssl

if __name__ == "__main__":
    import argparse
    import logs
    import textwrap

    import cli

    parser = argparse.ArgumentParser(description='Stand up an iRODS zone.')

    cli.add_common_args(parser)
    cli.add_compose_args(parser)
    cli.add_database_config_args(parser)
    cli.add_irods_package_args(parser)

    parser.add_argument('--use-ssl',
                        dest='use_ssl', action='store_true',
                        help=textwrap.dedent('''\
                            Indicates that SSL should be configured and enabled in the Zone.\
                            '''))

    args = parser.parse_args()

    if args.package_directory and args.package_version:
        print('--package-directory and --package-version are incompatible')
        exit(1)

    project_directory = os.path.abspath(args.project_directory or os.getcwd())

    ctx = context.context(docker.from_env(),
                          compose.cli.command.get_project(
                              project_dir=project_directory,
                              project_name=args.project_name))

    logs.configure(args.verbosity)

    # Bring up the services
    logging.debug('bringing up project [{}]'.format(ctx.compose_project.name))
    services.create_topology(ctx,
                             externals_directory=args.irods_externals_package_directory,
                             package_directory=args.package_directory,
                             package_version=args.package_version,
                             odbc_driver=args.odbc_driver,
                             consumer_count=3)

    if args.use_ssl:
        ssl.configure_ssl_in_zone(ctx.docker_client, ctx.compose_project)
