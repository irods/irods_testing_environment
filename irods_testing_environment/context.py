class context(object):
    """Class for holding Docker/Compose environment and container context information."""
    def __init__(self, docker_client=None, compose_project=None):
        """Construct a context object.

        Arguments:
        self -- required for object construction
        docker_client -- Docker client environment with which we communicate with the daemon
        compose_project -- compose.project information
        """
        import docker
        self.docker_client = docker_client or docker.from_env()
        self.compose_project = compose_project
        self.platform_image_tag = None
        self.database_image_tag = None

    def platform(self, platform_service_name=None, platform_service_instance=1):
        """Return platform Docker image from the specified service in `self.compose_project`.

        Arguments:
        platform_service_name -- service to target for platform derivation (default: provider)
        platform_service_instance -- service instance to target for platform derivation
        """
        if not self.platform_image_tag:
            self.platform_image_tag = base_image(self.docker_client.containers.get(
                container_name(self.compose_project.name,
                    platform_service_name or irods_catalog_provider_service(),
                    platform_service_instance)))

        return self.platform_image_tag.split('/')[-1]

    def database(self, database_service_instance=1):
        """Return database Docker image from the database service in `self.compose_project`.

        Arguments:
        database_service_instance -- service instance to target for database derivation
        """
        if not self.database_image_tag:
            self.database_image_tag = base_image(self.docker_client.containers.get(
                irods_catalog_database_container(self.compose_project.name)))

        return self.database_image_tag.split('/')[-1]

    def platform_name(self):
        """Return the repo name for the OS platform image for this Compose project."""
        return image_repo(self.platform())

    def database_name(self):
        """Return the repo name for the database image for this Compose project."""
        return image_repo(self.database())

    def irods_containers(self):
        """Return the set of containers running iRODS servers in this Compose project."""
        return [c for c in self.compose_project.containers()
                if not is_catalog_database_container(c)]

def is_database_plugin(package_name):
    """Return whether the provided package name is the iRODS database plugin package."""
    return 'irods-database-plugin-' in package_name


def irods_externals_package_names():
    """Return list of iRODS externals package names. For now, just a glob-able string."""
    return ['irods-externals']


def irods_package_names(database_name=None):
    """Return list of iRODS packages (with database plugin if `database_name` provided)."""
    irods_package_names = ['irods-runtime', 'irods-icommands', 'irods-server']

    if database_name:
        if database_name == 'mariadb':
            database_name = 'mysql'
        irods_package_names.append('irods-database-plugin-{}'.format(database_name))

    return irods_package_names


def irods_catalog_database_service():
    """Return name of the iRODS catalog database server docker-compose service."""
    return 'catalog'


def irods_catalog_provider_service():
    """Return name of the iRODS catalog service provider docker-compose service."""
    return 'irods-catalog-provider'


def irods_catalog_consumer_service():
    """Return name of the iRODS catalog service consumer docker-compose service."""
    return 'irods-catalog-consumer'


def irods_home():
    """Return the path to the iRODS Linux user's home directory."""
    import os
    return os.path.join('/var', 'lib', 'irods')


def irods_config():
    """Return the path to the iRODS configuration directory."""
    import os
    return os.path.join('/etc', 'irods')


def server_config():
    """Return the path to the iRODS server_config.json file."""
    import os
    return os.path.join(irods_config(), 'server_config.json')


def core_re():
    """Return the path to the iRODS core.re file."""
    import os
    return os.path.join(irods_config(), 'core.re')


def service_account_irods_env():
    """Return the path to the iRODS service account client environment file."""
    import os
    return os.path.join(irods_home(), '.irods', 'irods_environment.json')


def run_tests_script():
    """Return the path to the script which runs the python tests."""
    import os
    return os.path.join(irods_home(), 'scripts', 'run_tests.py')


def unit_tests():
    """Return the path to the directory containing packaged unit tests."""
    import os
    return os.path.join(irods_home(), 'unit_tests')


def sanitize(repo_or_tag):
    """Sanitize the input from special characters rejected by docker-compose.

    Arguments:
    repo_or_tag -- input string which should represent a docker image repo or tag
    """
    return (repo_or_tag.replace('.', '')
                       .replace(':', '')
                       .replace('/', ''))


def project_name(container_name):
    """Return the docker-compose project name based on the `container_name`.

    NOTE: docker-compose "sanitizes" project names to remove certain special characters, so the
    `--project-name` provided to `docker-compose` may be different from the project name used
    when constructed the name of the image(s) and container(s).

    Arguments:
    container_name -- the name of the container from which the project name is extracted
    """
    return container_name.split('_')[0]


def service_name(container_name):
    """Return the docker-compose project service name based on the `container_name`.

    Arguments:
    container_name -- the name of the container from which the service name is extracted
    """
    return container_name.split('_')[1]


def service_instance(container_name):
    """Return the service instance number based on the `container_name`.

    Arguments:
    container_name -- the name of the container from which the service instance is extracted
    """
    return int(container_name.split('_')[2])


def container_name(project_name, service_name, service_instance=1):
    """Return the name of the container as constructed by docker-compose.

    The passed in `project_name` will have dots (.) removed because docker-compose strips all
    dots from its project names. docker-compose container names are generated in three parts
    which are delimited by underscores, like this:
        project-name_service-name_service-instance-as-a-1-indexed-integer

    Arguments:
    project_name -- name of the docker-compose project (1)
    service_name -- name of the service in the docker-compose project (2)
    service_instance -- number of the instance of the service instance (3)
    """
    return '_'.join([sanitize(project_name), service_name, str(service_instance)])


def base_image(container, tag=0):
    """Return the base image for the specified docker.container.

    The base image is the last (read: oldest) item in the history() of a Docker image that has a
    valid ID (read: not "<missing>" or "sha256:<missing>").

    Arguments:
    container -- docker.container from which the OS platform is to be extracted
    tag -- The index in the list of Tags for the retrieved base Docker image (default: first)
    """
    return [image for image in
                container.client.images.get(
                    container.client.api.inspect_container(container.name)['Config']['Image']
                ).history()
            if '<missing>' not in image['Id']][-1]['Tags'][tag]


def container_hostname(container):
    """Return the hostname for the specified docker.container.

    Arguments:
    container -- docker.container from which the hostname is to be extracted
    """
    return container.client.api.inspect_container(container.name)['Config']['Hostname']


def container_ip(container, network_name=None):
    """Return the IP address for the specified docker.container.

    Arguments:
    container -- docker.container from which the IP is to be extracted
    network_name -- name of the docker network to inspect (if None, default network is used)
    """
    return (container.client.api.inspect_container(container.name)
        ['NetworkSettings']
        ['Networks']
        [network_name or '_'.join([project_name(container.name), 'default'])]
        ['IPAddress']
    )


def image_repo_and_tag_string(image_repo_and_tag):
    """Return the docker image repo and tag tuple as a string of the form `repo:tag`.

    If `image_repo_and_tag` is already a string, `image_repo_and_tag` is returned.

    Arguments:
    image_repo_and_tag -- a tuple containing the docker image repo and tag
    """
    if isinstance(image_tag, str):
        return image_repo_and_tag

    return ':'.join(image_repo_and_tag)


def image_repo_and_tag(image_repo_and_tag_string):
    """Split the docker image tag string into a list of docker image name and tag.

    Arguments:
    image_repo_and_tag_string -- a standard docker image tag string of the form `repo:tag`
    """
    if isinstance(image_repo_and_tag_string, list):
        return image_repo_and_tag_string

    return image_repo_and_tag_string.split(':')


def image_repo(image_repo_and_tag_string):
    """Return the name portion of a docker image tag string."""
    return image_repo_and_tag(image_repo_and_tag_string)[0]


def image_tag(image_repo_and_tag_string):
    """Return the tag portion of a docker image tag string."""
    return image_repo_and_tag(image_repo_and_tag_string)[1]


def irods_catalog_provider_container(project_name, service_instance=1):
    """Return the name of the container running the iRODS CSP for the specified project.

    Arguments:
    project_name -- name of the Compose project to inspect
    service_instance -- the service instance number for the iRODS CSP service
    """
    return container_name(project_name, irods_catalog_provider_service(), service_instance)


def irods_catalog_consumer_container(project_name, service_instance=1):
    """Return the name of the container running the iRODS CSC for the specified project.

    Arguments:
    project_name -- name of the Compose project to inspect
    service_instance -- the service instance number for the iRODS CSC service
    """
    return container_name(project_name, irods_catalog_consumer_service(), service_instance)


def irods_catalog_database_container(project_name, service_instance=1):
    """Return the name of the container running the database for the specified project.

    Arguments:
    project_name -- name of the Compose project to inspect
    service_instance -- the service instance number for the database service
    """
    return container_name(project_name, irods_catalog_database_service(), service_instance)


def is_catalog_database_container(container):
    """Return True if `container` is the database service. Otherwise, False."""
    return service_name(container.name) == irods_catalog_database_service()


def is_irods_catalog_provider_container(container):
    """Return True if `container` is the iRODS CSP service. Otherwise, False."""
    return service_name(container.name) == irods_catalog_provider_service()


def is_irods_catalog_consumer_container(container):
    """Return True if `container` is the iRODS CSC service. Otherwise, False."""
    return service_name(container.name) == irods_catalog_consumer_service()


def is_irods_server_in_local_zone(container, local_zone):
    """Return True if the iRODS Zone running in `container` matches the info in `local_zone`.

    Arguments:
    container -- the container to inspect (if not running iRODS, returns False)
    local_zone -- zone information against which to compare for the container running iRODS
    """
    if is_catalog_database_container(container):
        return False

    if is_irods_catalog_provider_container(container):
        return service_instance(container.name) is local_zone.provider_service_instance

    if is_irods_catalog_consumer_container(container):
        return service_instance(container.name) in local_zone.consumer_service_instances

    raise NotImplementedError('service name is not supported [{}]'.format(container.name))


def project_hostnames(docker_client, compose_project):
    """Return a map of container names to hostnames for the provided Compose project as a dict.

    Arguments:
    docker_client -- docker client for interacting with the docker-compose project
    compose_project -- compose.Project from which hostnames will be derived
    """
    return {
        c.name : container_hostname(docker_client.containers.get(c.name))
        for c in compose_project.containers()
    }
