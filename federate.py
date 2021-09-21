# grown-up modules
import compose.cli.command
import docker
import json
import logging
import os

# local modules
import context
import database_setup
import execute
import install
import irods_setup
import irods_config

def make_negotiation_key(local_zone_name, remote_zone_name=''):
    negotation_key_size_in_bytes = 32
    filler = '_' * negotation_key_size_in_bytes
    prefix = '_'.join([local_zone_name, remote_zone_name])
    return prefix + filler[:negotation_key_size_in_bytes - len(prefix)]


def make_zone_key(zone_name):
    zone_key_prefix = 'ZONE_KEY_FOR'
    return '_'.join([zone_key_prefix, zone_name])


def get_info_for_zones(ctx, zone_names, consumer_service_instances_per_zone=0):
    zone_info_list = list()

    for i, zn in enumerate(zone_names):
        # Divide up the consumers evenly amongst the Zones
        consumer_service_instances = [
            context.service_instance(c.name)
            for c in ctx.compose_project.containers()
            if context.is_irods_catalog_consumer_container(c)
            and context.service_instance(c.name) > i * consumer_service_instances_per_zone
            and context.service_instance(c.name) <= (i + 1) * consumer_service_instances_per_zone
        ]

        logging.debug('consumer service instances for [{}] [{}] (expected: [{}])'
                     .format(zn, consumer_service_instances,
                             list(range((i*consumer_service_instances_per_zone)+1,
                                        ((i+1)*consumer_service_instances_per_zone)+1))
                     ))

        zone_info_list.append(
            irods_setup.zone_info(database_service_instance=i + 1,
                                  provider_service_instance=i + 1,
                                  consumer_service_instances=consumer_service_instances,
                                  zone_name=zn,
                                  zone_key=make_zone_key(zn),
                                  negotiation_key=make_negotiation_key(zn))
        )

    return zone_info_list


def make_federation_entry(ctx, local_zone, remote_zone):
    # TODO: Need to have strategies for different version of iRODS, this only works for 4.1/4.2, I think?
    return {
        'catalog_provider_hosts': [remote_zone.provider_hostname(ctx)],
        'negotiation_key': make_negotiation_key(local_zone.zone_name, remote_zone.zone_name),
        'zone_key': make_zone_key(remote_zone.zone_name),
        'zone_name': remote_zone.zone_name,
        'zone_port': 1247
    }


def federate_zones(ctx, zone_info_list, local_zone, include_consumers=True):
    """Federate `local_zone` with each zone in `zone_info_list`.

    Arguments:
    ctx -- context object which contains information about the Docker environment
    zone_info_list -- list of iRODS Zone information for the Zones to federate
    local_zone -- the local zone federating with each zone in `zone_info_list`
    include_consumers -- if True, a Federation stanza will be included for every iRODS catalog
                         service consumer in `local_zone` in addition to the catalog service
                         provider (which is not optional in the federation configuration)
    """
    # Every iRODS server in the Zone must be federated
    for c in ctx.compose_project.containers():
        if not context.is_irods_server_in_local_zone(c, local_zone): continue

        if not include_consumers and context.is_irods_catalog_consumer_container(c): continue

        logging.debug('container [{}] zone [{}] provider instance [{}]'
                      .format(c.name,
                              local_zone.zone_name,
                              local_zone.provider_service_instance))

        container = ctx.docker_client.containers.get(c.name)

        server_config = irods_config.get_json_from_file(ctx, container, context.server_config())

        for remote_zone in zone_info_list:
            if remote_zone.zone_name == local_zone.zone_name: continue

            logging.warning('federating remote zone [{}] with local zone [{}] on [{}]'
                            .format(remote_zone.zone_name, local_zone.zone_name, container.name))

            server_config['federation'].append(make_federation_entry(ctx,
                                                                     local_zone,
                                                                     remote_zone))

            # Only make the remote Zone once per local Zone
            if context.is_irods_catalog_provider_container(container):
                make_remote_zone = 'iadmin mkzone {} remote {}:{}'.format(remote_zone.zone_name,
                                                                          remote_zone.provider_hostname(ctx),
                                                                          remote_zone.zone_port)

                if execute.execute_command(container, make_remote_zone, user='irods') is not 0:
                    raise RuntimeError('failed to create remote zone [{}]'
                                       .format(container.name))

        # Write out the server_config.json to the iRODS server container to complete the federation
        overwrite_server_config = 'bash -c \'echo "{}" > {}\''.format(
            json.dumps(server_config).replace('"', '\\"'), context.server_config())

        if execute.execute_command(container, overwrite_server_config) is not 0:
            raise RuntimeError('failed to update server_config [{}]'.format(container.name))


def form_federation_clique(ctx, zone_info_list, include_consumers=True):
    """Federate each zone in `zone_info_list` with every other zone in `zone_info_list`.

    Arguments:
    ctx - context which holds information about the Compose environment
    zone_info_list - list of information about Zones which will be federated with one another
    """
    import concurrent.futures

    rc = 0

    # configure federation between all zones (O(len(zone_names)^2))
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures_to_containers = {
            executor.submit(federate_zones, ctx, zone_info_list, z, include_consumers):
                z for z in zone_info_list
        }

        for f in concurrent.futures.as_completed(futures_to_containers):
            z = futures_to_containers[f]
            try:
                f.result()
                logging.debug('iRODS Zone federated successfully [{}]'.format(z.zone_name))

            except Exception as e:
                logging.error('exception raised while federating iRODS Zone [{}]'.format(z.zone_name))
                logging.error(e)
                rc = 1

    if rc is not 0:
        raise RuntimeError('failed to federate one or more iRODS Zones, ec=[{}]'.format(rc))


if __name__ == "__main__":
    import argparse
    import logs
    import textwrap

    import cli

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
        zone_info_list = get_info_for_zones(ctx, zone_names, args.consumers_per_zone)

        install.install_irods_packages(ctx,
                                       externals_directory=args.irods_externals_package_directory,
                                       package_directory=args.package_directory,
                                       package_version=args.package_version)

        irods_setup.setup_irods_zones(ctx, zone_info_list, odbc_driver=args.odbc_driver)

    else:
        zone_info_list = get_info_for_zones(ctx, zone_names, args.consumers_per_zone)

    form_federation_clique(ctx, zone_info_list, args.federate_consumers)

