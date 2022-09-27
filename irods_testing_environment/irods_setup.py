# grown-up modules
import compose
import docker
import logging
import os

# local modules
from . import context
from . import database_setup
from . import odbc_setup
from . import execute
from . import irods_config

class zone_info(object):
    """Class to hold information about an iRODS Zone and the containers running the servers."""
    def __init__(self,
                 zone_name='tempZone',
                 zone_key='TEMPORARY_ZONE_KEY',
                 negotiation_key='32_byte_server_negotiation_key__',
                 zone_port=1247,
                 database_service_instance=1,
                 provider_service_instance=1,
                 consumer_service_instances=None):
        """Construct a zone_info object.

        Arguments:
        zone_name -- name of the iRODS Zone
        zone_key -- zone_key for the iRODS Zone
        negotiation_key -- 32-byte negotiation_key for the iRODS Zone
        zone_port -- zone_port for the iRODS Zone
        database_service_instance -- service instance for the database container for this Zone
        provider_service_instance -- service instance for the iRODS CSP container for this Zone
        consumer_service_instances -- service instances for the iRODS Catalog Service Consumer
                                      containers for this Zone (if None is provided, all running
                                      iRODS Catalog Service Consumer service instances are
                                      determined to be part of this Zone, per the irods_setup
                                      interfaces. list() indicates that no iRODS Catalog
                                      Service Consumers are in this zone.
        """
        self.zone_name = zone_name
        self.zone_key = zone_key
        self.negotiation_key = negotiation_key
        self.zone_port = zone_port
        self.database_service_instance = database_service_instance
        self.provider_service_instance = provider_service_instance
        self.consumer_service_instances = consumer_service_instances

    def provider_hostname(self, ctx):
        """Return hostname for the container running the iRODS CSP."""
        return context.container_hostname(
            ctx.docker_client.containers.get(
                context.irods_catalog_provider_container(
                    ctx.compose_project.name,
                    service_instance=self.provider_service_instance)
            )
        )

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
        self.irods_version = None

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

        self.provides_local_storage = 'y'
        self.resource_name = ''
        self.vault_directory = ''

        self.catalog_service_provider_host = 'localhost'

    def setup(self,
              irods_version,
              service_account_name= None,
              service_account_group= None,
              catalog_service_role= None,
              odbc_driver= None,
              database_server_hostname= None,
              database_server_port= None,
              database_name= None,
              database_username= None,
              database_password= None,
              stored_passwords_salt= None,
              zone_name= None,
              catalog_service_provider_host= None,
              zone_port= None,
              parallel_port_range_begin= None,
              parallel_port_range_end= None,
              control_plane_port= None,
              schema_validation_base_uri= None,
              admin_username= None,
              zone_key = None,
              negotiation_key = None,
              control_plane_key = None,
              admin_password = None,
              provides_local_storage = None,
              resource_name = None,
              vault_directory = None):
        """Set values for the service account section of the setup script.

        Returns this instance of the class.

        Arguments:
        irods_version -- a tuple representing the version of iRODS being configured
        service_account_name -- linux account that will run the iRODS server
        service_account_group -- group of the linux account that will run the iRODS server
        catalog_service_role -- determines whether this server holds a connection to the catalog
        odbc_driver -- driver on the server used to talk to the ODBC database layer
        database_server_hostname -- hostname for the database server
        database_server_port -- port on which database server listens for notifications from
                                other applications
        database_name -- name of the database that we created in database setup
        database_username -- name of the database user
        database_password -- password for the database user
        stored_passwords_salt -- obfuscates the passwords stored in the database
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
        zone_key -- secret key used in server-to-server communication
        negotiation_key -- secret key used in server-to-server communication
        control_plane_key -- secret key shared by all servers
        admin_password -- password for the iRODS administration account
        provides_local_storage -- indicates whether the server should provide storage
        resource_name -- name used to identify the local storage
        vault_directory -- storage location of the default unixfilesystem resource created
                           during installation
        """
        self.irods_version = irods_version

        self.service_account_name = service_account_name or self.service_account_name
        self.service_account_group = service_account_group or self.service_account_group
        self.catalog_service_role = catalog_service_role or self.catalog_service_role

        self.odbc_driver = odbc_driver or self.odbc_driver
        self.database_server_hostname = database_server_hostname or self.database_server_hostname
        self.database_server_port = database_server_port or self.database_server_port
        self.database_name = database_name or self.database_name
        self.database_username = database_username or self.database_username
        self.database_password = database_password or self.database_password
        self.stored_passwords_salt = stored_passwords_salt or self.stored_passwords_salt

        self.zone_name = zone_name or self.zone_name
        self.catalog_service_provider_host = catalog_service_provider_host or self.catalog_service_provider_host
        self.zone_port = zone_port or self.zone_port
        self.parallel_port_range_begin = parallel_port_range_begin or self.parallel_port_range_begin
        self.parallel_port_range_end = parallel_port_range_end or self.parallel_port_range_end
        self.control_plane_port = control_plane_port or self.control_plane_port
        self.schema_validation_base_uri = schema_validation_base_uri or self.schema_validation_base_uri
        self.admin_username = admin_username or self.admin_username

        self.zone_key = zone_key or self.zone_key
        self.negotiation_key = negotiation_key or self.negotiation_key
        self.control_plane_key = control_plane_key or self.control_plane_key
        self.admin_password = admin_password or self.admin_password

        self.provides_local_storage = provides_local_storage or self.provides_local_storage
        self.resource_name = resource_name or self.resource_name
        self.vault_directory = vault_directory or self.vault_directory

        return self


    def build_input_for_catalog_consumer(self):
        """Generate string to use as input for the setup script.

        The script changes depending on the role, so the options used here are specific to
        setting up an iRODS catalog service consumer.
        """
        # The setup script defaults catalog service consumer option as 2
        role = 2
        input_args = [
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
            '' # confirmation of inputs
        ]

        # Handle the difference between 4.2 servers and 4.3 servers.
        if self.irods_version >= (4, 3, 0):
            input_args.insert(3, str(self.provides_local_storage))
            input_args.insert(4, str(self.resource_name))
            input_args.insert(5, str(self.vault_directory))
        else:
            input_args.append(str(self.vault_directory))
            input_args.append(str('')) # final confirmation

        return '\n'.join(input_args)

    def build_input_for_catalog_provider(self):
        """Generate string to use as input for the setup script.

        The script changes depending on the role, so the options used here are specific to
        setting up an iRODS catalog service provider.
        """
        role = ''
        input_args = [
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
            '' # confirmation of inputs
        ]

        # Handle the difference between 4.2 servers and 4.3 servers.
        if self.irods_version >= (4, 3, 0):
            input_args.insert(11, str(self.provides_local_storage))
            input_args.insert(12, str(self.resource_name))
            input_args.insert(13, str(self.vault_directory))
        else:
            input_args.append(str(self.vault_directory))
            input_args.append(str('')) # final confirmation

        return '\n'.join(input_args)

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


def configure_rsyslog(container):
    def restart_rsyslog(container):
        rsyslog_bin_path = os.path.join('/usr', 'sbin', 'rsyslogd')

        ec = execute.execute_command(container, f'pkill {os.path.basename(rsyslog_bin_path)}')
        if ec != 0:
            logging.info(f'[{container.name}] failed to kill rsyslogd')

        ec = execute.execute_command(container, rsyslog_bin_path)
        if ec != 0:
            raise RuntimeError(f'[{container.name}] failed to start rsyslogd')

    import textwrap
    rsyslog_config_file = os.path.join('/etc', 'rsyslog.d', '00-irods.conf')
    rsyslog_config_contents = textwrap.dedent('''\
        \$FileCreateMode 0644
        \$DirCreateMode 0755
        \$Umask 0000
        \$template irods_format,\\"%msg%\\n\\"
        :programname,startswith,\\"irodsServer\\" /var/log/irods/irods.log;irods_format
        & stop
        :programname,startswith,\\"irodsDelayServer\\" /var/log/irods/irods.log;irods_format
        & stop''')

    ec = execute.execute_command(container, f'bash -c \'echo "{rsyslog_config_contents}" > {rsyslog_config_file}\'')
    if ec != 0:
        raise RuntimeError(f'[{container.name}] failed to configure rsyslog')

    logrotate_config_file = os.path.join('/etc', 'logrotate.d', 'irods')
    logrotate_config_contents = textwrap.dedent('''\
	/var/log/irods/irods.log {
	    weekly
	    rotate 26
	    copytruncate
	    delaycompress
	    compress
	    dateext
	    notifempty
	    missingok
	    su root root
	}''')

    ec = execute.execute_command(container, f'bash -c \'echo "{logrotate_config_contents}" > {logrotate_config_file}\'')
    if ec != 0:
        raise RuntimeError(f'[{container.name}] failed to configure logrotate')

    restart_rsyslog(container)


def stop_irods(container):
    irodsctl = os.path.join(context.irods_home(), 'irodsctl')
    return execute.execute_command(container, f'{irodsctl} stop', user='irods')


def restart_irods(container):
    irodsctl = os.path.join(context.irods_home(), 'irodsctl')
    return execute.execute_command(container, f'{irodsctl} restart', user='irods')


def setup_irods_server(container, setup_input):
    """Set up iRODS server on the given container with the provided input.

    After setup completes, rsyslog is restarted to ensure that log messages are being processed
    and then the server is restarted in order to guarantee that the iRODS server is running and
    available for immediate use after setting it up.

    Arguments:
    container -- docker.client.container on which the iRODS packages are installed
    setup_input -- string which will be provided as input to the iRODS setup script
    """
    from . import container_info
    from . import irods_config

    if stop_irods(container) != 0:
        logging.debug(f'[{container.name}] failed to stop iRODS server before setup')

    ec = execute.execute_command(container, 'bash -c \'echo "{}" > /input\''.format(setup_input))
    if ec != 0:
        raise RuntimeError('failed to create setup script input file [{}]'.format(container.name))

    execute.execute_command(container, 'cat /input')

    path_to_setup_script = os.path.join(context.irods_home(), 'scripts', 'setup_irods.py')
    run_setup_script = 'bash -c \'{} {} < /input\''.format(container_info.python(container),
                                                           path_to_setup_script)
    ec = execute.execute_command(container, run_setup_script)
    if ec != 0:
        raise RuntimeError('failed to set up iRODS server [{}]'.format(container.name))

    # Only configure rsyslog for versions later than 4.3.0 as this was the first release
    # which uses syslog. In the future, maybe the syslog implementation used in the
    # testing environment can be swapped out.
    version_triple = irods_config.get_irods_version(container)
    if version_triple[0] >= 4 and version_triple[1] >= 3:
        configure_rsyslog(container)

    if restart_irods(container) != 0:
        raise RuntimeError(f'[{container.name}] failed to start iRODS server after setup')


def setup_irods_catalog_provider(ctx,
                                 database_service_instance=1,
                                 provider_service_instance=1,
                                 odbc_driver=None,
                                 **kwargs):
    """Set up iRODS catalog service provider in a docker-compose project.

    Arguments:
    database_service_instance -- the service instance number of the container running the
                                 database server
    provider_service_instance -- the service instance number of the container being targeted
                                 to run the iRODS catalog service provider
    odbc_driver -- path to the local archive file containing the ODBC driver
    """
    csp_container = ctx.docker_client.containers.get(
        context.irods_catalog_provider_container(
            ctx.compose_project.name, provider_service_instance
        )
    )

    odbc_setup.configure_odbc_driver(ctx.platform(), ctx.database(), csp_container, odbc_driver)

    db_container = ctx.docker_client.containers.get(
        context.irods_catalog_database_container(
            ctx.compose_project.name, provider_service_instance
        )
    )

    setup_input = (setup_input_builder()
        .setup(irods_version=irods_config.get_irods_version(csp_container),
               catalog_service_role='provider',
               database_server_hostname=context.container_hostname(db_container),
               database_server_port=database_setup.database_server_port(ctx.database()),
               **kwargs
        )
        .build()
    )

    logging.debug('input to setup script [{}]'.format(setup_input))

    logging.warning('setting up iRODS catalog provider [{}]'.format(csp_container.name))

    setup_irods_server(csp_container, setup_input)


def setup_irods_catalog_consumer(ctx,
                                 provider_service_instance=1,
                                 consumer_service_instance=1,
                                 **kwargs):
    """Set up iRODS catalog service consumer in a docker-compose project.

    Arguments:
    provider_service_instance -- the service instance number of the container running the iRODS
                                 catalog service provider
    consumer_service_instance -- the service instance number of the containers being targeted
                                 to run the iRODS catalog service consumer
    """
    csp_container = ctx.docker_client.containers.get(
        context.irods_catalog_provider_container(
            ctx.compose_project.name, provider_service_instance
        )
    )

    csc_container = ctx.docker_client.containers.get(
        context.irods_catalog_consumer_container(
            ctx.compose_project.name, consumer_service_instance
        )
    )

    setup_input = (setup_input_builder()
        .setup(irods_version=irods_config.get_irods_version(csc_container),
               catalog_service_role='consumer',
               catalog_service_provider_host=context.container_hostname(csp_container),
               **kwargs)
        .build()
    )

    logging.debug('input to setup script [{}]'.format(setup_input))

    logging.warning('setting up iRODS catalog consumer [{}]'
                    .format(csc_container.name))

    setup_irods_server(csc_container, setup_input)


def setup_irods_catalog_consumers(ctx,
                                  provider_service_instance=1,
                                  consumer_service_instances=None,
                                  **kwargs):
    """Set up all iRODS catalog service consumers in a docker-compose project in parallel.

    Arguments:
    provider_service_instance -- the service instance for the iRODS catalog service provider
                                 running in this docker-compose project
    consumer_service_instances -- the service instance number of the containers being targeted
                                  to run the iRODS catalog service consumer. If None is
                                  provided, all containers with the iRODS catalog service
                                  consumer service name in the Compose project will be
                                  targeted. If an empty list is provided, nothing happens.
    """
    import concurrent.futures

    catalog_consumer_containers = ctx.compose_project.containers(
        service_names=[context.irods_catalog_consumer_service()])

    if consumer_service_instances:
        if len(consumer_service_instances) is 0:
            logging.warning('empty list of iRODS catalog service consumers to set up')
            return

        consumer_service_instances = [
            context.service_instance(c.name)
            for c in catalog_consumer_containers
            if context.service_instance(c.name) in consumer_service_instances
        ]
    else:
        consumer_service_instances = [
            context.service_instance(c.name) for c in catalog_consumer_containers
        ]

    rc = 0

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures_to_catalog_consumer_instances = {
            executor.submit(
                setup_irods_catalog_consumer,
                ctx, provider_service_instance, instance, **kwargs
            ): instance for instance in consumer_service_instances
        }

        logging.debug(futures_to_catalog_consumer_instances)

        for f in concurrent.futures.as_completed(futures_to_catalog_consumer_instances):
            i = futures_to_catalog_consumer_instances[f]
            container_name = context.irods_catalog_consumer_container(ctx.compose_project.name,
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

def setup_irods_zone(ctx,
                     force_recreate=False,
                     provider_service_instance=1,
                     database_service_instance=1,
                     consumer_service_instances=None,
                     odbc_driver=None,
                     **kwargs):
    """Set up an iRODS Zone with the specified settings on the specified service instances.

    Arguments:
    provider_service_instance -- the service instance for the iRODS catalog service provider
                                 running in this docker-compose project
    database_service_instance -- the service instance number of the container running the
                                 database server
    consumer_service_instances -- the service instance number of the containers being targeted
                                  to run the iRODS catalog service consumer. If None is
                                  provided, all containers with the iRODS catalog service
                                  consumer service name in the Compose project will be
                                  targeted. If an empty list is provided, nothing happens.
    odbc_driver -- path to the local archive file containing the ODBC driver
    """
    database_setup.wait_for_database_service(
        ctx, database_service_instance=database_service_instance)

    logging.info('setting up catalog database [{}]'.format(database_service_instance))
    database_setup.setup_catalog(ctx,
                                 force_recreate=force_recreate,
                                 service_instance=database_service_instance)

    logging.info('setting up catalog provider [{}] [{}]'.format(provider_service_instance,
                                                                database_service_instance))
    setup_irods_catalog_provider(ctx,
                                 database_service_instance=database_service_instance,
                                 provider_service_instance=provider_service_instance,
                                 odbc_driver=odbc_driver,
                                 **kwargs)

    logging.info('setting up catalog consumers [{}] [{}]'.format(provider_service_instance,
                                                                 consumer_service_instances))
    setup_irods_catalog_consumers(ctx,
                                  provider_service_instance=provider_service_instance,
                                  consumer_service_instances=consumer_service_instances,
                                  **kwargs)

def setup_irods_zones(ctx,
                      zone_info_list,
                      odbc_driver=None):
    import concurrent.futures

    rc = 0

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures_to_containers = {
            executor.submit(setup_irods_zone,
                            ctx,
                            provider_service_instance=z.provider_service_instance,
                            database_service_instance=z.database_service_instance,
                            consumer_service_instances=z.consumer_service_instances,
                            odbc_driver=odbc_driver,
                            zone_name=z.zone_name,
                            zone_key=z.zone_key,
                            negotiation_key=z.negotiation_key,
            ): z for i, z in enumerate(zone_info_list)
        }

        for f in concurrent.futures.as_completed(futures_to_containers):
            zone = futures_to_containers[f]
            try:
                f.result()
                logging.debug('iRODS Zone setup completed successfully [{}]'.format(zone))

            except Exception as e:
                logging.error('exception raised while setting up iRODS Zone [{}]'.format(zone))
                logging.error(e)
                rc = 1

    if rc is not 0:
        raise RuntimeError('failed to set up one or more iRODS Zones, ec=[{}]'.format(rc))


def make_negotiation_key(local_zone_name, remote_zone_name=''):
    negotation_key_size_in_bytes = 32
    filler = '_' * negotation_key_size_in_bytes
    # TODO: need predictable way to generate unique keys
    #prefix = '_'.join([local_zone_name, remote_zone_name])
    #return prefix + filler[:negotation_key_size_in_bytes - len(prefix)]
    return filler


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

        logging.info('consumer service instances for [{}] [{}] (expected: [{}])'
                     .format(zn, consumer_service_instances,
                             list(range((i*consumer_service_instances_per_zone)+1,
                                        ((i+1)*consumer_service_instances_per_zone)+1))
                     ))

        zone_info_list.append(
            zone_info(database_service_instance=i + 1,
                      provider_service_instance=i + 1,
                      consumer_service_instances=consumer_service_instances,
                      zone_name=zn,
                      zone_key=make_zone_key(zn),
                      negotiation_key=make_negotiation_key(zn))
        )

    return zone_info_list
