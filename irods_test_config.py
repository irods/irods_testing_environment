# grown-up modules
import compose.cli.command
import docker
import logging
import os

# local modules
import context
import execute

def configure_hosts_config(docker_client, compose_project):
    """Set hostname aliases for all iRODS servers in the compose project via hosts_config.json.

    Arguments:
    docker_client -- docker client for interacting with the docker-compose project
    compose_project -- compose.Project in which the iRODS servers are running
    """
    import json
    def set_hostnames(docker_client, docker_compose_container, hosts_file):
        container = docker_client.containers.get(docker_compose_container.name)

        if context.is_irods_catalog_provider_container(container):
            alias = 'icat.example.org'
        else:
            alias = 'resource{}.example.org'.format(
                context.service_instance(docker_compose_container.name))

        hosts = {
            'host_entries': [
                {
                    'address_type': 'local',
                    'addresses': [
                        {'address': context.container_ip(container)},
                        {'address': context.container_hostname(container)},
                        {'address': alias}
                    ]
                }
            ]
        }

        for o in containers:
            if o.name == container.name: continue

            other = docker_client.containers.get(o.name)

            if context.is_irods_catalog_provider_container(other):
                remote_address = 'icat.example.org'
            else:
                remote_address = 'resource{}.example.org'.format(
                    context.service_instance(other.name))

            hosts['host_entries'].append(
                {
                    'address_type': 'remote',
                    'addresses': [
                        {'address': context.container_ip(other)},
                        {'address': context.container_hostname(other)},
                        {'address': remote_address}
                    ]
                }
            )

        logging.info('json for hosts_config [{}] [{}]'.format(json.dumps(hosts), container.name))

        create_hosts_config = 'bash -c \'echo "{}" > {}\''.format(
            json.dumps(hosts).replace('"', '\\"'), hosts_file)

        if execute.execute_command(container, create_hosts_config) is not 0:
            raise RuntimeError('failed to create hosts_config file [{}]'.format(container.name))

        return 0

    import concurrent.futures

    containers = compose_project.containers(service_names=[
        context.irods_catalog_provider_service(),
        context.irods_catalog_consumer_service()])

    rc = 0
    with concurrent.futures.ThreadPoolExecutor() as executor:
        hosts_file = os.path.join('/etc', 'irods', 'hosts_config.json')
        futures_to_containers = {
            executor.submit(set_hostnames, docker_client, c, hosts_file): c for c in containers
        }
        logging.debug(futures_to_containers)

        for f in concurrent.futures.as_completed(futures_to_containers):
            container = futures_to_containers[f]
            try:
                ec = f.result()
                if ec is not 0:
                    logging.error('error while configuring hosts_configs.json on container [{}]'
                                  .format(container.name))
                    rc = ec
                else:
                    logging.info('hosts_config.json configured successfully [{}]'
                                 .format(container.name))

            except Exception as e:
                logging.error('exception raised while installing packages [{}]'
                              .format(container.name))
                logging.error(e)
                rc = 1

    if rc is not 0:
        raise RuntimeError('failed to configure hosts_config.json on some service')


def configure_univmss_script(docker_client, compose_project):
    """Configure UnivMSS script for iRODS tests.

    Arguments:
    docker_client -- docker client for interacting with the docker-compose project
    compose_project -- compose.Project in which the iRODS servers are running
    """
    def modify_script(docker_client, docker_compose_container, script):
        chown_msiexec = 'chown irods:irods {}'.format(os.path.dirname(univmss_script))
        copy_from_template = 'cp {0}.template {0}'.format(univmss_script)
        remove_template_from_commands = 'sed -i \"s/template-//g\" {}'.format(univmss_script)
        make_script_executable = 'chmod 544 {}'.format(univmss_script)

        on_container = docker_client.containers.get(docker_compose_container.name)
        if execute.execute_command(on_container,
                                   chown_msiexec) is not 0:
            raise RuntimeError('failed to change ownership to msiExecCmd_bin [{}]'
                               .format(on_container.name))

        if execute.execute_command(on_container,
                                   copy_from_template,
                                   user='irods',
                                   workdir=context.irods_home()) is not 0:
            raise RuntimeError('failed to copy univMSSInterface.sh template file [{}]'
                               .format(on_container.name))

        if execute.execute_command(on_container,
                                   remove_template_from_commands,
                                   user='irods',
                                   workdir=context.irods_home()) is not 0:
            raise RuntimeError('failed to modify univMSSInterface.sh template file [{}]'
                               .format(on_container.name))

        if execute.execute_command(on_container,
                                   make_script_executable,
                                   user='irods',
                                   workdir=context.irods_home()) is not 0:
            raise RuntimeError('failed to change permissions on univMSSInterface.sh [{}]'
                               .format(on_container.name))

        return 0

    import concurrent.futures

    containers = compose_project.containers(service_names=[
        context.irods_catalog_provider_service(),
        context.irods_catalog_consumer_service()])

    rc = 0
    with concurrent.futures.ThreadPoolExecutor() as executor:
        univmss_script = os.path.join(
            context.irods_home(), 'msiExecCmd_bin', 'univMSSInterface.sh')

        futures_to_containers = {
            executor.submit(
                modify_script, docker_client, c, univmss_script
            ): c for c in containers
        }

        logging.debug(futures_to_containers)

        for f in concurrent.futures.as_completed(futures_to_containers):
            container = futures_to_containers[f]
            try:
                ec = f.result()
                if ec is not 0:
                    logging.error('error while configuring univMSS script on container [{}]'
                                  .format(container.name))
                    rc = ec
                else:
                    logging.info('univMSS script configured successfully [{}]'.format(container.name))

            except Exception as e:
                logging.error('exception raised while configuring univMSS script [{}]'.format(container.name))
                logging.error(e)
                rc = 1

    if rc is not 0:
        raise RuntimeError('failed to configure univMSS script on some service')


def configure_irods_testing(docker_client, compose_project):
    """Run a series of prerequisite configuration steps for iRODS tests.

    Arguments:
    docker_client -- docker client for interacting with the docker-compose project
    compose_project -- compose.Project in which the iRODS servers are running
    """
    configure_hosts_config(docker_client, compose_project)

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
