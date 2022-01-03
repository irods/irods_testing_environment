# grown-up modules
import argparse
import compose.cli.command
import docker
import logging
import os
import textwrap

# local modules
from irods_testing_environment import archive
from irods_testing_environment import context
from irods_testing_environment import irods_config
from irods_testing_environment import irods_setup
from irods_testing_environment import logs
from irods_testing_environment import ssl
from irods_testing_environment import test_utils
from irods_testing_environment.install import install

import cli

parser = argparse.ArgumentParser(description='Run iRODS plugin test hooks in a consistent environment.')

cli.add_common_args(parser)
cli.add_compose_args(parser)
cli.add_database_config_args(parser)
cli.add_irods_package_args(parser)
cli.add_irods_test_args(parser)
cli.add_irods_plugin_args(parser)

parser.add_argument('--skip-setup',
                    action='store_false', dest='do_setup',
                    help='If indicated, the iRODS servers will not be set up.')

parser.add_argument('--leak-containers',
                    action='store_false', dest='cleanup_containers',
                    help='If indicated, the containers will not be torn down.')

parser.add_argument('--test-hook-path',
                    metavar='PATH_TO_TEST_HOOK_FILE',
                    dest='test_hook',
                    help='Path to local test hook file to run.')

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
    if args.do_setup:
        # Bring up the services
        logging.debug('bringing up project [{}]'.format(ctx.compose_project.name))
        consumer_count = 0
        # TODO: may need to extend container privileges to allow for mungefs, etc.
        containers = ctx.compose_project.up(scale_override={
            context.irods_catalog_consumer_service(): consumer_count
        })

        install.make_installer(ctx.platform_name()).install_irods_packages(
            ctx,
            externals_directory=args.irods_externals_package_directory,
            package_directory=args.package_directory,
            package_version=args.package_version)

        irods_setup.setup_irods_zone(ctx, odbc_driver=args.odbc_driver)

        # Configure the containers for running iRODS automated tests
        logging.info('configuring iRODS containers for testing')
        irods_config.configure_irods_testing(ctx.docker_client, ctx.compose_project)

    # Get the container on which the command is to be executed
    container = ctx.docker_client.containers.get(
        context.container_name(ctx.compose_project.name,
                               context.irods_catalog_provider_service(),
                               service_instance=1)
    )

    plugin_package_directory = os.path.abspath(args.plugin_package_directory)

    archive.copy_archive_to_container(container,
                                      archive.create_archive(
                                          [plugin_package_directory],
                                          args.plugin_name))

    options = ['--output_root_directory', output_directory,
               '--built_packages_root_directory', plugin_package_directory]

    if args.test_hook:
        rc = test_utils.run_test_hook_file(container, args.test_hook, options)
    else:
        rc = test_utils.run_test_hook(container,
                                      args.plugin_name,
                                      branch='4-2-stable',
                                      options=options)

except Exception as e:
    logging.critical(e)

    raise

finally:
    logging.warning('collecting logs [{}]'.format(output_directory))
    logs.collect_logs(ctx.docker_client, ctx.irods_containers(), output_directory)

    if args.cleanup_containers:
        ctx.compose_project.down(include_volumes=True, remove_image_type=False)

exit(rc)
