# grown-up modules
import compose.cli.command
import docker
import logging
import os

# local modules
import context
import execute

def reconnect_with_alias(container, network, alias):
    network.disconnect(container)
    network.connect(container, aliases=[alias])


def set_hostnames_for_irods(docker_client, compose_project):
    # Assuming only the default network is in use for all services
    network_name = list(compose_project.services[0].networks.keys())[0]
    network = docker_client.networks.get(
        list(n.id for n in docker_client.networks.list() if n.name == network_name)[0])

    hosts_file = os.path.join('/etc', 'hosts')

    # TODO: PARALLEL
    containers = compose_project.containers(service_names=[
        context.irods_catalog_provider_service(),
        context.irods_catalog_consumer_service()])
    for c in containers:
        container = docker_client.containers.get(c.name)

        if context.is_irods_catalog_provider_container(container):
            alias = 'icat.example.org'
        else:
            alias = 'resource{}.example.org'.format(context.service_instance(c.name))

        # TODO: need to have each container recognize itself as `alias`
        # TODO: use /etc/irods/hosts_config.json!!
        # this does not work because the docker daemon is controlling the /etc/hosts file
        add_to_hosts_file = 'sed -i \'${{s/$/\\t{}/}}\' {}'.format(alias, hosts_file)
        if execute.execute_command(container, add_to_hosts_file) is not 0:
            raise RuntimeError('failed to add hostname [{}]'.format(c.name))

        reconnect_with_alias(container, network, alias)

def configure_univmss_script(docker_client, compose_project):
    """Configure UnivMSS script for iRODS tests.

    Arguments:
    docker_client -- docker client for interacting with the docker-compose project
    compose_project -- compose.Project in which the iRODS servers are running
    """
    # TODO: PARALLEL
    univmss_script = os.path.join(context.irods_home(),
                                  'msiExecCmd_bin',
                                  'univMSSInterface.sh')
    chown_msiexec = 'chown irods:irods {}'.format(os.path.dirname(univmss_script))
    copy_from_template = 'cp {0}.template {0}'.format(univmss_script)
    remove_template_from_commands = 'sed -i \"s/template-//g\" {}'.format(univmss_script)
    make_script_executable = 'chmod 544 {}'.format(univmss_script)

    containers = compose_project.containers(service_names=[
        context.irods_catalog_provider_service(),
        context.irods_catalog_consumer_service()])

    for c in containers:
        on_container = docker_client.containers.get(c.name)
        if execute.execute_command(on_container,
                                   chown_msiexec) is not 0:
            raise RuntimeError('failed to change ownership to msiExecCmd_bin [{}]'
                               .format(c.name))

        if execute.execute_command(on_container,
                                   copy_from_template,
                                   user='irods',
                                   workdir=context.irods_home()) is not 0:
            raise RuntimeError('failed to copy univMSSInterface.sh template file [{}]'
                               .format(c.name))

        if execute.execute_command(on_container,
                                   remove_template_from_commands,
                                   user='irods',
                                   workdir=context.irods_home()) is not 0:
            raise RuntimeError('failed to modify univMSSInterface.sh template file [{}]'
                               .format(c.name))

        if execute.execute_command(on_container,
                                   make_script_executable,
                                   user='irods',
                                   workdir=context.irods_home()) is not 0:
            raise RuntimeError('failed to change permissions on univMSSInterface.sh [{}]'
                               .format(c.name))


def configure_irods_testing(docker_client, compose_project):
    """Run a series of prerequisite configuration steps for iRODS tests.

    Arguments:
    docker_client -- docker client for interacting with the docker-compose project
    compose_project -- compose.Project in which the iRODS servers are running
    """
    set_hostnames_for_irods(docker_client, compose_project)

    configure_univmss_script(docker_client, compose_project)

if __name__ == "__main__":
    import argparse
    import logs

    parser = argparse.ArgumentParser(description='Run iRODS tests in a consistent environment.')
    parser.add_argument('--project-directory', metavar='PATH_TO_PROJECT_DIRECTORY', type=str, dest='project_directory', default='.',
                        help='Path to the docker-compose project on which packages will be installed.')
    parser.add_argument('--project-name', metavar='PROJECT_NAME', type=str, dest='project_name',
                        help='Name of the docker-compose project on which to install packages.')
    parser.add_argument('--os-platform-image', '-p', metavar='OS_PLATFORM_IMAGE_REPO_AND_TAG', dest='platform', type=str,
                        help='The repo:tag of the OS platform image to use')
    parser.add_argument('--database-image', '-d', metavar='DATABASE_IMAGE_REPO_AND_TAG', dest='database', type=str,
                        help='The repo:tag of the database image to use')
    parser.add_argument('--verbose', '-v', dest='verbosity', action='count', default=1,
                        help='Increase the level of output to stdout. CRITICAL and ERROR messages will always be printed.')

    args = parser.parse_args()

    docker_client = docker.from_env()

    compose_project = compose.cli.command.get_project(os.path.abspath(args.project_directory),
                                                      project_name=args.project_name)

    logs.configure(args.verbosity)

    project_name = args.project_name or compose_project.name

    platform = args.platform
    if not platform:
        platform = context.image_repo_and_tag_string(
            context.platform_image_repo_and_tag(project_name)
        )

        logging.debug('derived os platform image tag [{}]'.format(platform))

    database = args.database
    if not database:
        database = context.image_repo_and_tag_string(
            context.database_image_repo_and_tag(project_name))

        logging.debug('derived database image tag [{}]'.format(database))

    try:
        configure_irods_testing(docker_client, compose_project)

    except Exception as e:
        logging.critical(e)
        exit(1)
