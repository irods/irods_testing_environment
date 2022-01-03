# grown-up modules
import compose.cli.command
import docker
import logging
import os

# local modules
import archive
import context
import execute
import services

if __name__ == "__main__":
    import argparse
    import logs
    import textwrap

    import cli

    parser = argparse.ArgumentParser(description='Install iRODS packages to a docker-compose project.')

    cli.add_common_args(parser)
    cli.add_compose_args(parser)
    cli.add_irods_package_args(parser)

    args = parser.parse_args()

    if args.package_directory and args.package_version:
        print('package directory and package version are mutually exclusive')
        exit(1)

    logs.configure(args.verbosity)

    project_directory = os.path.abspath(args.project_directory or os.getcwd())

    ctx = context.context(docker.from_env(),
                          compose.cli.command.get_project(
                              project_dir=project_directory,
                              project_name=args.project_name))

    logging.debug('provided project name [{0}], docker-compose project name [{1}]'
                  .format(args.project_name, ctx.compose_project.name))

    if len(ctx.compose_project.containers()) is 0:
        logging.critical(
            'no containers found for project [directory=[{0}], name=[{1}]]'.format(
            os.path.abspath(project_directory), ctx.compose_project.name))

        exit(1)

    exit(install_irods_packages(ctx,
                                externals_directory=args.irods_externals_package_directory,
                                package_directory=args.package_directory,
                                package_version=args.package_version)
    )
