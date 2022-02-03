# grown-up modules
import compose.cli.command
import docker
import json
import logging
import os

# local modules
from irods_testing_environment import context
from irods_testing_environment import database_setup
from irods_testing_environment import execute
from irods_testing_environment import irods_setup
from irods_testing_environment import irods_config
from irods_testing_environment import json_utils
from irods_testing_environment import federate
from irods_testing_environment.install import install

if __name__ == "__main__":
    import argparse
    import textwrap

    import cli
    from irods_testing_environment import logs

    parser = argparse.ArgumentParser(description='Stand up and federate two or more iRODS zones.')

    cli.add_common_args(parser)
    cli.add_compose_args(parser)
    cli.add_database_config_args(parser)
    cli.add_irods_package_args(parser)

    parser.add_argument('--consumers-per-zone',
                        metavar='IRODS_CATALOG_CONSUMER_INSTANCES_PER_ZONE',
                        dest='consumers_per_zone', type=int, default=0,
                        help=textwrap.dedent('''\
                            Number of iRODS Catalog Service Consumer service instances per \
                            Zone.'''))

    parser.add_argument('--federate-consumers',
                        dest='federate_consumers', action='store_true',
                        help=textwrap.dedent('''\
                            If indicated, the iRODS Catalog Service Consumers for each Zone \
                            will be federated with each of the other Zones in addition to the \
                            iRODS Catalog Service Providers (which are required to be \
                            federated).'''))

    parser.add_argument('--zone-names',
                        metavar='IRODS_ZONE_NAME',
                        nargs='+', dest='zone_names',
                        help='Space-delimited list of zone names to set up.')

    parser.add_argument('--skip-setup',
                        action='store_false', dest='do_setup',
                        help='If indicated, the Zones will not be set up, only federated.')

    args = parser.parse_args()

    if args.package_directory and args.package_version:
        print('--package-directory and --package-version are incompatible')
        exit(1)

    zone_names = args.zone_names or ['tempZone', 'otherZone']

    project_directory = os.path.abspath(args.project_directory or os.getcwd())

    ctx = context.context(docker.from_env(),
                          compose.cli.command.get_project(
                              project_dir=project_directory,
                              project_name=args.project_name))

    logs.configure(args.verbosity)

    zone_count = len(zone_names)
    consumer_count = args.consumers_per_zone * zone_count

    if args.do_setup:
        # Bring up the services
        logging.debug('bringing up project [{}]'.format(ctx.compose_project.name))
        containers = ctx.compose_project.up(scale_override={
            context.irods_catalog_database_service(): zone_count,
            context.irods_catalog_provider_service(): zone_count,
            context.irods_catalog_consumer_service(): consumer_count
        })

        # The catalog consumers are only determined after the containers are running
        zone_info_list = federate.get_info_for_zones(ctx, zone_names, args.consumers_per_zone)

        install.make_installer(ctx.platform_name()).install_irods_packages(
            ctx,
            externals_directory=args.irods_externals_package_directory,
            package_directory=args.package_directory,
            package_version=args.package_version)

        irods_setup.setup_irods_zones(ctx, zone_info_list, odbc_driver=args.odbc_driver)

    else:
        zone_info_list = federate.get_info_for_zones(ctx, zone_names, args.consumers_per_zone)

    federate.form_federation_clique(ctx, zone_info_list, args.federate_consumers)

