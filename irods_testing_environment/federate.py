# grown-up modules
import logging

# local modules
from . import context
from . import execute
from . import irods_setup
from . import json_utils


def make_federation_entry(ctx, local_zone, remote_zone):
    """Create an entry for the federation stanza to federate two zones together.

    Arguments:
    ctx -- context object which contains information about the Docker environment
    local_zone -- name of the local iRODS zone
    remote_zone -- name of the remote iRODS zone with which `local_zone` is federating
    """
    # TODO: Need to have strategies for different version of iRODS, this only works for 4.1/4.2, I think?
    negotiation_key_prefix = "_".join(
        sorted([local_zone.zone_name, remote_zone.zone_name])
    )
    return {
        "catalog_provider_hosts": [remote_zone.provider_hostname(ctx)],
        "negotiation_key": irods_setup.make_negotiation_key(negotiation_key_prefix),
        "zone_key": irods_setup.make_zone_key(remote_zone.zone_name),
        "zone_name": remote_zone.zone_name,
        "zone_port": 1247,
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
        if not context.is_irods_server_in_local_zone(c, local_zone):
            continue

        if not include_consumers and context.is_irods_catalog_consumer_container(c):
            continue

        logging.debug(
            "container [{}] zone [{}] provider instance [{}]".format(
                c.name, local_zone.zone_name, local_zone.provider_service_instance
            )
        )

        container = ctx.docker_client.containers.get(c.name)

        server_config = json_utils.get_json_from_file(
            container, context.server_config()
        )

        for remote_zone in zone_info_list:
            if remote_zone.zone_name == local_zone.zone_name:
                continue

            logging.warning(
                "federating remote zone [{}] with local zone [{}] on [{}]".format(
                    remote_zone.zone_name, local_zone.zone_name, container.name
                )
            )

            server_config["federation"].append(
                make_federation_entry(ctx, local_zone, remote_zone)
            )

            # Only make the remote Zone once per local Zone
            if context.is_irods_catalog_provider_container(container):
                make_remote_zone = "iadmin mkzone {} remote {}:{}".format(
                    remote_zone.zone_name,
                    remote_zone.provider_hostname(ctx),
                    remote_zone.zone_port,
                )

                if (
                    execute.execute_command(container, make_remote_zone, user="irods")
                    != 0
                ):
                    raise RuntimeError(
                        "failed to create remote zone [{}]".format(container.name)
                    )

        # Write out the server_config.json to the iRODS server container to complete the federation
        json_utils.put_json_to_file(container, context.server_config(), server_config)


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
            executor.submit(
                federate_zones, ctx, zone_info_list, z, include_consumers
            ): z
            for z in zone_info_list
        }

        for f in concurrent.futures.as_completed(futures_to_containers):
            z = futures_to_containers[f]
            try:
                f.result()
                logging.debug(
                    "iRODS Zone federated successfully [{}]".format(z.zone_name)
                )

            except Exception as e:
                logging.error(
                    "exception raised while federating iRODS Zone [{}]".format(
                        z.zone_name
                    )
                )
                logging.error(e)
                rc = 1

    if rc != 0:
        raise RuntimeError(
            "failed to federate one or more iRODS Zones, ec=[{}]".format(rc)
        )
