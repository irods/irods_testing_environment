# grown-up modules
import compose
import docker
import logging
import os

# local modules
import context
import database_setup
import odbc_setup
import execute

class setup_input_builder(object):
    """Builder for iRODS setup script inputs.

    The builder is designed to look like a programmable interface to the iRODS setup script.
    To that end, each section of the setup script is its own method which sets the values
    to generate the input string.
    """
    def __init__(self):
        """Construct a setup input builder.

        Sets default values for the setup script inputs.
        """
        self.service_account_name = ''
        self.service_account_group = ''
        self.catalog_service_role = ''

        self.odbc_driver = ''
        self.database_server_hostname = 'localhost'
        self.database_server_port = 5432
        self.database_name = 'ICAT'
        self.database_username = 'irods'
        self.database_password = 'testpassword'
        self.stored_passwords_salt = ''

        self.zone_name = 'tempZone'
        self.zone_port = 1247
        self.parallel_port_range_begin = 20000
        self.parallel_port_range_end = 20199
        self.control_plane_port = 1248
        self.schema_validation_base_uri = ''
        self.admin_username = 'rods'

        self.zone_key = 'TEMPORARY_ZONE_KEY'
        self.negotiation_key = '32_byte_server_negotiation_key__'
        self.control_plane_key = '32_byte_server_control_plane_key'
        self.admin_password = 'rods'

        self.vault_directory = ''

        self.catalog_service_provider_host = 'localhost'

    def service_account(self,
                        service_account_name='',
                        service_account_group='',
                        catalog_service_role=''):
        """Set values for the service account section of the setup script.

        Returns this instance of the class.

        Arguments:
        service_account_name -- linux account that will run the iRODS server
        service_account_group -- group of the linux account that will run the iRODS server
        catalog_service_role -- determines whether this server holds a connection to the catalog
        """
        self.service_account_name = service_account_name
        self.service_account_group = service_account_group
        self.catalog_service_role = catalog_service_role

        return self


    def database_connection(self,
                            odbc_driver='',
                            database_server_hostname='localhost',
                            database_server_port=5432,
                            database_name='ICAT',
                            database_username='irods',
                            database_password='testpassword',
                            stored_passwords_salt=''):
        """Set values for the database connection section of the setup script.

        Returns this instance of the class.

        Arguments:
        odbc_driver -- driver on the server used to talk to the ODBC database layer
        database_server_hostname -- hostname for the database server
        database_server_port -- port on which database server listens for notifications from
                                other applications
        database_name -- name of the database that we created in database setup
        database_username -- name of the database user
        database_password -- password for the database user
        stored_passwords_salt -- obfuscates the passwords stored in the database
        """
        self.odbc_driver = odbc_driver
        self.database_server_hostname = database_server_hostname
        self.database_server_port = database_server_port
        self.database_name = database_name
        self.database_username = database_username
        self.database_password = database_password
        self.stored_passwords_salt = stored_passwords_salt

        return self


    def server_options(self,
                       zone_name='tempZone',
                       catalog_service_provider_host='localhost',
                       zone_port=1247,
                       parallel_port_range_begin=20000,
                       parallel_port_range_end=20199,
                       control_plane_port=1248,
                       schema_validation_base_uri='',
                       admin_username='rods'):
        """Set values for the server options section of the setup script.

        Returns this instance of the class.

        Arguments:
        zone_name -- name of the iRODS zone
        catalog_service_provider_host -- hostname for the iRODS catalog service provider (only
                                         applicable when setting up a catalog service consumer)
        zone_port -- main iRODS port
        parallel_port_range_begin -- beginning of the port range used when transferring large
                                     files
        parallel_port_range_end -- end of the port range used when transferring large files
        control_plane_port -- port used for the control plane
        schema_validation_base_uri -- location of the schema files used to validate the server's
                                      configuration files
        admin_username -- name of the iRODS administration account
        """
        self.zone_name = zone_name
        self.catalog_service_provider_host = catalog_service_provider_host
        self.zone_port = zone_port
        self.parallel_port_range_begin = parallel_port_range_begin
        self.parallel_port_range_end = parallel_port_range_end
        self.control_plane_port = control_plane_port
        self.schema_validation_base_uri = schema_validation_base_uri
        self.admin_username = admin_username

        return self


    def keys_and_passwords(self,
                           zone_key = 'TEMPORARY_ZONE_KEY',
                           negotiation_key = '32_byte_server_negotiation_key__',
                           control_plane_key = '32_byte_server_control_plane_key',
                           admin_password = 'rods'):
        """Set values for the keys and passwords section of the setup script.

        Arguments:
        zone_key -- secret key used in server-to-server communication
        negotiation_key -- secret key used in server-to-server communication
        control_plane_key -- secret key shared by all servers
        admin_password -- password for the iRODS administration account
        """
        self.zone_key = zone_key
        self.negotiation_key = negotiation_key
        self.control_plane_key = control_plane_key
        self.admin_password = admin_password

        return self


    def vault_directory(self, vault_directory=''):
        """Set value for the vault directory section of the setup script.

        Arguments:
        vault_directory -- storage location of the default unixfilesystem resource created
                           during installation
        """
        self.vault_directory = vault_directory

        return self


    def build_input_for_catalog_consumer(self):
        """Generate string to use as input for the setup script.

        The script changes depending on the role, so the options used here are specific to
        setting up an iRODS catalog service consumer.
        """
        # The setup script defaults catalog service consumer option as 2
        role = 2
        return '\n'.join([
            str(self.service_account_name),
            str(self.service_account_group),
            str(role),

            str(self.zone_name),
            str(self.catalog_service_provider_host),
            str(self.zone_port),
            str(self.parallel_port_range_begin),
            str(self.parallel_port_range_end),
            str(self.control_plane_port),
            str(self.schema_validation_base_uri),
            str(self.admin_username),
            'y', # confirmation of inputs

            str(self.zone_key),
            str(self.negotiation_key),
            str(self.control_plane_key),
            str(self.admin_password),
            '', #confirmation of inputs

            str(self.vault_directory),
            '' # confirmation of inputs
        ])

    def build_input_for_catalog_provider(self):
        """Generate string to use as input for the setup script.

        The script changes depending on the role, so the options used here are specific to
        setting up an iRODS catalog service provider.
        """
        role = ''
        return '\n'.join([
            str(self.service_account_name),
            str(self.service_account_group),
            str(role),

            str(self.odbc_driver),
            str(self.database_server_hostname),
            str(self.database_server_port),
            str(self.database_name),
            str(self.database_username),
            'y', # confirmation of inputs
            str(self.database_password),
            str(self.stored_passwords_salt),

            str(self.zone_name),
            str(self.zone_port),
            str(self.parallel_port_range_begin),
            str(self.parallel_port_range_end),
            str(self.control_plane_port),
            str(self.schema_validation_base_uri),
            str(self.admin_username),
            'y', # confirmation of inputs

            str(self.zone_key),
            str(self.negotiation_key),
            str(self.control_plane_key),
            str(self.admin_password),
            '', # confirmation of inputs

            str(self.vault_directory),
            '' # final confirmation
        ])

    def build(self):
        """Build the string for the setup script input.

        Depending on the way the inputs were provided, either an iRODS catalog service provider
        or a catalog service consumer will be set up and the resulting input string will be
        returned.
        """
        build_for_role = {
            'provider': self.build_input_for_catalog_provider,
            'consumer': self.build_input_for_catalog_consumer
        }

        try:
            return build_for_role[self.catalog_service_role]()

        except KeyError:
            raise NotImplementedError('unsupported catalog service role [{}]'.format(self.catalog_service_role))


def setup_irods_server(container, setup_input):
    """Set up iRODS server on the given container with the provided input.

    After setup completes, the server is restarted in order to guarantee that the iRODS server
    is running and available for immediate use after setting it up.

    Arguments:
    container -- docker.client.container on which the iRODS packages are installed
    setup_input -- string which will be provided as input to the iRODS setup script
    """
    irodsctl = os.path.join(context.irods_home(), 'irodsctl')
    ec = execute.execute_command(container, '{} stop'.format(irodsctl), user='irods')
    if ec is not 0:
        logging.debug('failed to stop iRODS server before setup [{}]'.format(container.name))

    ec = execute.execute_command(container, 'bash -c \'echo "{}" > /input\''.format(setup_input))
    if ec is not 0:
        raise RuntimeError('failed to create setup script input file [{}]'.format(container.name))

    execute.execute_command(container, 'cat /input')

    path_to_setup_script = os.path.join(context.irods_home(), 'scripts', 'setup_irods.py')
    run_setup_script = 'bash -c \'python {0} < /input\''.format(path_to_setup_script)
    ec = execute.execute_command(container, run_setup_script)
    if ec is not 0:
        raise RuntimeError('failed to set up iRODS server [{}]'.format(container.name))

    ec = execute.execute_command(container, '{} restart'.format(irodsctl), user='irods')
    if ec is not 0:
        raise RuntimeError('failed to start iRODS server after setup [{}]'.format(container.name))


def setup_irods_catalog_provider(docker_client,
                                 compose_project,
                                 platform_image,
                                 database_image,
                                 database_service_instance=1,
                                 provider_service_instance=1,
                                 odbc_driver=None):
    """Set up iRODS catalog service provider in a docker-compose project.

    Arguments:
    docker_client -- docker client for interacting with the docker-compose project
    compose_project -- compose.project in which the iRODS catalog provider is running
    platform_image -- repo:tag for the docker image of the platform running the iRODS servers
    database_image -- repo:tag for the docker image of the database server
    database_service_instance -- the service instance number of the container running the
                                 database server
    provider_service_instance -- the service instance number of the container being targeted
                                 to run the iRODS catalog service provider
    odbc_driver -- path to the local archive file containing the ODBC driver
    """
    csp_container = docker_client.containers.get(
        context.irods_catalog_provider_container(
            compose_project.name, provider_service_instance
        )
    )

    odbc_setup.configure_odbc_driver(platform_image, database_image, csp_container, odbc_driver)

    db_container = docker_client.containers.get(
        context.irods_catalog_database_container(
            compose_project.name, provider_service_instance
        )
    )

    setup_input = (setup_input_builder()
        .service_account(catalog_service_role='provider')
        .database_connection(
            database_server_hostname=context.container_hostname(db_container),
            database_server_port=database_setup.database_server_port(database_image)
        )
        .build()
    )

    logging.debug('input to setup script [{}]'.format(setup_input))

    logging.warning('setting up iRODS catalog provider [{}]'.format(csp_container.name))

    setup_irods_server(csp_container, setup_input)


def setup_irods_catalog_consumer(docker_client,
                                 compose_project,
                                 platform_image,
                                 database_image,
                                 provider_service_instance=1,
                                 consumer_service_instance=1):
    """Set up iRODS catalog service consumer in a docker-compose project.

    Arguments:
    docker_client -- docker client for interacting with the docker-compose project
    compose_project -- compose.project in which the iRODS catalog provider is running
    platform_image -- repo:tag for the docker image of the platform running the iRODS servers
    database_image -- repo:tag for the docker image of the database server
    provider_service_instance -- the service instance number of the container running the iRODS
                                 catalog service provider
    consumer_service_instance -- the service instance number of the containers being targeted
                                 to run the iRODS catalog service consumer
    """
    csp_container = docker_client.containers.get(
        context.irods_catalog_provider_container(
            compose_project.name, provider_service_instance
        )
    )

    setup_input = (setup_input_builder()
        .service_account(catalog_service_role='consumer')
        .server_options(catalog_service_provider_host=context.container_hostname(csp_container))
        .build()
    )

    logging.debug('input to setup script [{}]'.format(setup_input))

    csc_container = docker_client.containers.get(
        context.irods_catalog_consumer_container(
            compose_project.name, consumer_service_instance
        )
    )

    logging.warning('setting up iRODS catalog consumer [{}]'.format(csc_container.name))

    setup_irods_server(csc_container, setup_input)

def setup_irods_catalog_consumers(docker_client,
                                  compose_project,
                                  platform_image,
                                  database_image,
                                  provider_service_instance=1,
                                  consumer_service_instances=None):
    """Set up all iRODS catalog service consumers in a docker-compose project in parallel.

    Arguments:
    docker_client -- docker client for interacting with the docker-compose project
    compose_project -- compose.project in which the iRODS catalog provider is running
    platform_image -- repo:tag for the docker image of the platform running the iRODS servers
    database_image -- repo:tag for the docker image of the database server
    provider_service_instance -- the service instance for the iRODS catalog service provider
                                 running in this docker-compose project
    consumer_service_instances -- the service instance number of the containers being targeted
                                  to run the iRODS catalog service consumer (if None, all
                                  containers with the iRODS catalog service consumer service
                                  name in the docker project will be targeted)
    """
    import concurrent.futures

    csc_containers = compose_project.containers(
        service_names=[context.irods_catalog_consumer_service()])

    if consumer_service_instances:
        consumer_service_instances = [context.service_instance(c.name) for c in csc_containers
            if context.service_instance(c.name) in consumer_service_instances]
    else:
        consumer_service_instances = [i + 1 for i in range(len(csc_containers))]

    rc = 0

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures_to_containers = {
            executor.submit(
                setup_irods_catalog_consumer,
                docker_client,
                compose_project,
                platform_image,
                database_image,
                provider_service_instance,
                instance
            ): instance for instance in consumer_service_instances
        }

        logging.debug(futures_to_containers)

        for f in concurrent.futures.as_completed(futures_to_containers):
            i = futures_to_containers[f]
            container_name = context.irods_catalog_consumer_container(compose_project.name,
                                                                      i + 1)
            try:
                f.result()
                logging.debug('setup completed successfully [{}]'.format(container_name))

            except Exception as e:
                logging.error('exception raised while setting up iRODS [{}]'
                              .format(container_name))
                logging.error(e)
                rc = 1

    if rc is not 0:
        raise RuntimeError('failed to set up one or more catalog service consumers, ec=[{}]'
                           .format(rc))
