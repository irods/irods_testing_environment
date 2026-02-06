# grown-up modules
import compose
import docker
import json
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


    def provider_container(self, ctx):
        """Return Docker Container running the iRODS CSP."""
        return ctx.docker_client.containers.get(
            context.irods_catalog_provider_container(
                ctx.compose_project.name,
                service_instance=self.provider_service_instance)
        )


    def consumer_container(self, ctx, instance):
        """Return Docker Container running an iRODS CSC with specified instance."""
        return ctx.docker_client.containers.get(
            context.irods_catalog_consumer_container(
                ctx.compose_project.name,
                service_instance=instance)
        )


    def consumer_containers(self, ctx):
        """Return list of Docker Containers running the iRODS CSCs."""
        return [self.consumer_container(ctx, i) for i in self.consumer_service_instances]


    def provider_hostname(self, ctx):
        """Return hostname for the container running the iRODS CSP."""
        return context.container_hostname(self.provider_container(ctx))


    def consumer_hostname(self, ctx, instance):
        """Return hostname for the container running an iRODS CSC with specified instance."""
        return context.container_hostname(
            ctx.docker_client.containers.get(
                context.irods_catalog_provider_container(
                    ctx.compose_project.name,
                    service_instance=instance)
            )
        )


    def consumer_hostnames(self, ctx):
        """Return list of hostnames for the containers running the iRODS CSCs."""
        return [self.consumer_hostname(ctx, i) for i in self.consumer_service_instances]


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

        self.host = None

        self.database_technology = None
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
              host = None,
              database_technology = None,
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
              vault_directory = None,
              **kwargs):
        """Set values for the service account section of the setup script.

        Returns this instance of the class.

        Arguments:
        irods_version -- a tuple representing the version of iRODS being configured
        service_account_name -- linux account that will run the iRODS server
        service_account_group -- group of the linux account that will run the iRODS server
        catalog_service_role -- determines whether this server holds a connection to the catalog
        host -- IP, FQDN, or hostname which identifies the iRODS server
        database_technology -- name of database technology used to store catalog information.
                               e.g. postgres, mysql, oracle
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

        self.host = host or self.host

        self.database_technology = database_technology or self.database_technology
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

        self.do_unattended_install = kwargs.get('do_unattended_install', False)

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

        # Handle the difference between 4.3 servers and 5.x servers.
        if self.irods_version >= (4, 90, 0):
            # Always remove the element at the highest index first to reduce
            # complexity around indices.
            del input_args[14] # Control plane key
            del input_args[8]  # Control plane port
            del input_args[8]  # Schema validation base URI

            # Insert entries for iRODS 5.x.
            input_args.insert(0, '') # Hostname

            # Insert entries for iRODS 4.3.
            input_args.insert(4, str(self.provides_local_storage))
            input_args.insert(5, str(self.resource_name))
            input_args.insert(6, str(self.vault_directory))
        # Handle the difference between 4.2 servers and 4.3 servers.
        elif self.irods_version >= (4, 3, 0):
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

            # TLDR: Always accept the default input argument. Expects an integer
            # instead of a filesystem path.
            #
            # The following used to be str(self.odbc_driver) as it would always
            # result in an empty string. Since adding support for unattended installs,
            # the input is now hard-coded to an empty string to avoid issues with this
            # style of setup.
            #
            # This function assumes that ODBC drivers are configured before the
            # creation of the input file.
            '',
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

        # Handle the difference between 4.3 servers and 5.x servers.
        if self.irods_version >= (4, 90, 0):
            # Remove entries that do not apply to iRODS 5.
            # Always remove the element at the highest index first to reduce
            # complexity around indices.
            del input_args[21] # Control plane key
            del input_args[15] # Control plane port
            del input_args[15] # Schema validation base URI

            # Insert entries for iRODS 5.x.
            input_args.insert(0, '') # Hostname

            # Insert entries for iRODS 4.3.
            input_args.insert(12, str(self.provides_local_storage))
            input_args.insert(13, str(self.resource_name))
            input_args.insert(14, str(self.vault_directory))
        # Handle the difference between 4.2 servers and 4.3 servers.
        elif self.irods_version >= (4, 3, 0):
            input_args.insert(11, str(self.provides_local_storage))
            input_args.insert(12, str(self.resource_name))
            input_args.insert(13, str(self.vault_directory))
        else:
            input_args.append(str(self.vault_directory))
            input_args.append(str('')) # final confirmation

        return '\n'.join(input_args)

    def build_unattended_install_input_for_catalog_consumer(self):
        """Generate JSON string to use as input for the setup script (unattended install).

        The script changes depending on the role, so the options used here are specific to
        setting up an iRODS catalog service consumer.
        """
        # Start with an iRODS 5 configuration.
        # While using the member variables of the builder is a nice to have, we've chosen
        # to hard-code most things to avoid unnecessary complexity. There aren't any known
        # test cases which require us to deviate from the standard configuration. It is
        # common for tests to modify server_config.json to meet their needs.
        json_input = {
            "admin_password": self.admin_password,
            "default_resource_directory": '/var/lib/irods/Vault',
            "default_resource_name": self.resource_name,
            "host_system_information": {
                "service_account_user_name": 'irods',
                "service_account_group_name": 'irods'
            },
            "service_account_environment": {
                "irods_client_server_policy": "CS_NEG_REFUSE",
                "irods_connection_pool_refresh_time_in_seconds": 300,
                "irods_cwd": f"/{self.zone_name}/home/{self.admin_username}",
                "irods_default_hash_scheme": "SHA256",
                "irods_default_number_of_transfer_threads": 4,
                "irods_default_resource": self.resource_name,
                "irods_encryption_algorithm": "AES-256-CBC",
                "irods_encryption_key_size": 32,
                "irods_encryption_num_hash_rounds": 16,
                "irods_encryption_salt_size": 8,
                "irods_home": f"/{self.zone_name}/home/{self.admin_username}",
                "irods_host": self.host,
                "irods_match_hash_policy": "compatible",
                "irods_maximum_size_for_single_buffer_in_megabytes": 32,
                "irods_port": self.zone_port,
                "irods_transfer_buffer_size_for_parallel_transfer_in_megabytes": 4,
                "irods_user_name": self.admin_username,
                "irods_zone_name": self.zone_name,
                "schema_name": "service_account_environment",
                "schema_version": "v5"
            },
            "server_config": {
                "advanced_settings": {
                    "checksum_read_buffer_size_in_bytes": 1048576,
                    "default_number_of_transfer_threads": 4,
                    "default_temporary_password_lifetime_in_seconds": 120,
                    "delay_rule_executors": [],
                    "delay_server_sleep_time_in_seconds": 30,
                    "dns_cache": {
                        "eviction_age_in_seconds": 3600,
                        "cache_clearer_sleep_time_in_seconds": 600,
                        "shared_memory_size_in_bytes": 5000000
                    },
                    "hostname_cache": {
                        "eviction_age_in_seconds": 3600,
                        "cache_clearer_sleep_time_in_seconds": 600,
                        "shared_memory_size_in_bytes": 2500000
                    },
                    "maximum_size_for_single_buffer_in_megabytes": 32,
                    "maximum_size_of_delay_queue_in_bytes": 0,
                    "maximum_temporary_password_lifetime_in_seconds": 1000,
                    "migrate_delay_server_sleep_time_in_seconds": 5,
                    "number_of_concurrent_delay_rule_executors": 4,
                    "stacktrace_file_processor_sleep_time_in_seconds": 10,
                    "transfer_buffer_size_for_parallel_transfer_in_megabytes": 4,
                    "transfer_chunk_size_for_parallel_transfer_in_megabytes": 40
                },
                "catalog_provider_hosts": [
                    self.catalog_service_provider_host
                ],
                "catalog_service_role": "consumer",
                "client_server_policy": "CS_NEG_REFUSE",
                "connection_pool_refresh_time_in_seconds": 300,
                "controlled_user_connection_list": {
                    "control_type": "denylist",
                    "users": []
                },
                "default_dir_mode": "0750",
                "default_file_mode": "0600",
                "default_hash_scheme": "SHA256",
                "default_resource_name": self.resource_name,
                "encryption": {
                    "algorithm": "AES-256-CBC",
                    "key_size": 32,
                    "num_hash_rounds": 16,
                    "salt_size": 8
                },
                "environment_variables": {},
                "federation": [],
                "graceful_shutdown_timeout_in_seconds": 30,
                "host": self.host,
                "host_access_control": {
                    "access_entries": []
                },
                "host_resolution": {
                    "host_entries": []
                },
                "log_level": {
                    "agent": "info",
                    "agent_factory": "info",
                    "api": "info",
                    "authentication": "info",
                    "database": "info",
                    "delay_server": "info",
                    "genquery1": "info",
                    "genquery2": "info",
                    "legacy": "info",
                    "microservice": "info",
                    "network": "info",
                    "resource": "info",
                    "rule_engine": "info",
                    "server": "info",
                    "sql": "info"
                },
                "match_hash_policy": "compatible",
                "negotiation_key": self.negotiation_key,
                "plugin_configuration": {
                    "authentication": {},
                    # TODO(irods/irods#8670): Is it okay to include an empty "database" stanza?
                    "network": {},
                    "resource": {},
                    "rule_engines": [
                        {
                            "instance_name": "irods_rule_engine_plugin-irods_rule_language-instance",
                            "plugin_name": "irods_rule_engine_plugin-irods_rule_language",
                            "plugin_specific_configuration": {
                                "re_data_variable_mapping_set": [
                                    "core"
                                ],
                                "re_function_name_mapping_set": [
                                    "core"
                                ],
                                "re_rulebase_set": [
                                    "core"
                                ],
                                "regexes_for_supported_peps": [
                                    "ac[^ ]*",
                                    "msi[^ ]*",
                                    "[^ ]*pep_[^ ]*_(pre|post|except|finally)"
                                ]
                            },
                            "shared_memory_instance": "irods_rule_language_rule_engine"
                        },
                        {
                            "instance_name": "irods_rule_engine_plugin-cpp_default_policy-instance",
                            "plugin_name": "irods_rule_engine_plugin-cpp_default_policy",
                            "plugin_specific_configuration": {}
                        }
                    ]
                },
                "rule_engine_namespaces": [
                    ""
                ],
                "schema_name": "server_config",
                "schema_version": "v5",
                "server_port_range_end": self.parallel_port_range_end,
                "server_port_range_start": self.parallel_port_range_begin,
                "zone_auth_scheme": "native",
                "zone_key": self.zone_key,
                "zone_name": self.zone_name,
                "zone_port": self.zone_port,
                "zone_user": self.admin_username
            }
        }

        if self.irods_version < (4, 90, 0):
            # Remove iRODS 5 configuration.
            json_input["server_config"].pop("client_server_policy", None)
            json_input["server_config"].pop("connection_pool_refresh_time_in_seconds", None)
            json_input["server_config"].pop("encryption", None)
            json_input["server_config"].pop("graceful_shutdown_timeout_in_seconds", None)
            json_input["server_config"].pop("host", None)
            json_input["server_config"]["log_level"].pop("genquery1", None)

            # Add iRODS 4.3 configuration.
            json_input["service_account_environment"].update({
                "irods_client_server_negotiation": "request_server_negotiation",
                "irods_server_control_plane_encryption_algorithm": "AES-256-CBC",
                "irods_server_control_plane_encryption_num_hash_rounds": 16,
                "irods_server_control_plane_key": "32_byte_server_control_plane_key",
                "irods_server_control_plane_port": 1248,
                "irods_server_control_plane_timeout_milliseconds": 10000,
                "schema_version": "v4"
            })
            json_input["server_config"]["advanced_settings"]["agent_factory_watcher_sleep_time_in_seconds"] = 5
            json_input["server_config"]["client_api_allowlist_policy"] = "enforce"
            json_input["server_config"].update({
                "schema_validation_base_uri": "file:///var/lib/irods/configuration_schemas",
                "schema_version": "v4",
                "server_control_plane_encryption_algorithm": "AES-256-CBC",
                "server_control_plane_encryption_num_hash_rounds": 16,
                "server_control_plane_key": "32_byte_server_control_plane_key",
                "server_control_plane_port": 1248,
                "server_control_plane_timeout_milliseconds": 10000
            })

        return json.dumps(json_input, sort_keys=True, indent=4)


    def build_unattended_install_input_for_catalog_provider(self):
        """Generate JSON string to use as input for the setup script (unattended install).

        The script changes depending on the role, so the options used here are specific to
        setting up an iRODS catalog service provider.
        """
        # Start with an iRODS 5 configuration.
        # While using the member variables of the builder is a nice to have, we've chosen
        # to hard-code most things to avoid unnecessary complexity. There aren't any known
        # test cases which require us to deviate from the standard configuration. It is
        # common for tests to modify server_config.json to meet their needs.
        json_input = {
            "admin_password": self.admin_password,
            "default_resource_directory": '/var/lib/irods/Vault',
            "default_resource_name": 'demoResc',
            "host_system_information": {
                "service_account_user_name": 'irods',
                "service_account_group_name": 'irods'
            },
            "service_account_environment": {
                "irods_client_server_policy": "CS_NEG_REFUSE",
                "irods_connection_pool_refresh_time_in_seconds": 300,
                "irods_cwd": f"/{self.zone_name}/home/{self.admin_username}",
                "irods_default_hash_scheme": "SHA256",
                "irods_default_number_of_transfer_threads": 4,
                "irods_default_resource": "demoResc",
                "irods_encryption_algorithm": "AES-256-CBC",
                "irods_encryption_key_size": 32,
                "irods_encryption_num_hash_rounds": 16,
                "irods_encryption_salt_size": 8,
                "irods_home": f"/{self.zone_name}/home/{self.admin_username}",
                "irods_host": self.host,
                "irods_match_hash_policy": "compatible",
                "irods_maximum_size_for_single_buffer_in_megabytes": 32,
                "irods_port": self.zone_port,
                "irods_transfer_buffer_size_for_parallel_transfer_in_megabytes": 4,
                "irods_user_name": self.admin_username,
                "irods_zone_name": self.zone_name,
                "schema_name": "service_account_environment",
                "schema_version": "v5"
            },
            "server_config": {
                "advanced_settings": {
                    "checksum_read_buffer_size_in_bytes": 1048576,
                    "default_number_of_transfer_threads": 4,
                    "default_temporary_password_lifetime_in_seconds": 120,
                    "delay_rule_executors": [],
                    "delay_server_sleep_time_in_seconds": 30,
                    "dns_cache": {
                        "eviction_age_in_seconds": 3600,
                        "cache_clearer_sleep_time_in_seconds": 600,
                        "shared_memory_size_in_bytes": 5000000
                    },
                    "hostname_cache": {
                        "eviction_age_in_seconds": 3600,
                        "cache_clearer_sleep_time_in_seconds": 600,
                        "shared_memory_size_in_bytes": 2500000
                    },
                    "maximum_size_for_single_buffer_in_megabytes": 32,
                    "maximum_size_of_delay_queue_in_bytes": 0,
                    "maximum_temporary_password_lifetime_in_seconds": 1000,
                    "migrate_delay_server_sleep_time_in_seconds": 5,
                    "number_of_concurrent_delay_rule_executors": 4,
                    "stacktrace_file_processor_sleep_time_in_seconds": 10,
                    "transfer_buffer_size_for_parallel_transfer_in_megabytes": 4,
                    "transfer_chunk_size_for_parallel_transfer_in_megabytes": 40
                },
                "catalog_provider_hosts": [
                    self.host
                ],
                "catalog_service_role": "provider",
                "client_server_policy": "CS_NEG_REFUSE",
                "connection_pool_refresh_time_in_seconds": 300,
                "controlled_user_connection_list": {
                    "control_type": "denylist",
                    "users": []
                },
                "default_dir_mode": "0750",
                "default_file_mode": "0600",
                "default_hash_scheme": "SHA256",
                "default_resource_name": "demoResc",
                "encryption": {
                    "algorithm": "AES-256-CBC",
                    "key_size": 32,
                    "num_hash_rounds": 16,
                    "salt_size": 8
                },
                "environment_variables": {},
                "federation": [],
                "graceful_shutdown_timeout_in_seconds": 30,
                "host": self.host,
                "host_access_control": {
                    "access_entries": []
                },
                "host_resolution": {
                    "host_entries": []
                },
                "log_level": {
                    "agent": "info",
                    "agent_factory": "info",
                    "api": "info",
                    "authentication": "info",
                    "database": "info",
                    "delay_server": "info",
                    "genquery1": "info",
                    "genquery2": "info",
                    "legacy": "info",
                    "microservice": "info",
                    "network": "info",
                    "resource": "info",
                    "rule_engine": "info",
                    "server": "info",
                    "sql": "info"
                },
                "match_hash_policy": "compatible",
                "negotiation_key": self.negotiation_key,
                "plugin_configuration": {
                    "authentication": {},
                    "database": {
                        "technology": self.database_technology,
                        "host": self.database_server_hostname,
                        "name": self.database_name,
                        "odbc_driver": self.odbc_driver,
                        "password": self.database_password,
                        "port": self.database_server_port,
                        "username": self.database_username
                    },
                    "network": {},
                    "resource": {},
                    "rule_engines": [
                        {
                            "instance_name": "irods_rule_engine_plugin-irods_rule_language-instance",
                            "plugin_name": "irods_rule_engine_plugin-irods_rule_language",
                            "plugin_specific_configuration": {
                                "re_data_variable_mapping_set": [
                                    "core"
                                ],
                                "re_function_name_mapping_set": [
                                    "core"
                                ],
                                "re_rulebase_set": [
                                    "core"
                                ],
                                "regexes_for_supported_peps": [
                                    "ac[^ ]*",
                                    "msi[^ ]*",
                                    "[^ ]*pep_[^ ]*_(pre|post|except|finally)"
                                ]
                            },
                            "shared_memory_instance": "irods_rule_language_rule_engine"
                        },
                        {
                            "instance_name": "irods_rule_engine_plugin-cpp_default_policy-instance",
                            "plugin_name": "irods_rule_engine_plugin-cpp_default_policy",
                            "plugin_specific_configuration": {}
                        }
                    ]
                },
                "rule_engine_namespaces": [
                    ""
                ],
                "schema_name": "server_config",
                "schema_version": "v5",
                "server_port_range_end": self.parallel_port_range_end,
                "server_port_range_start": self.parallel_port_range_begin,
                "zone_auth_scheme": "native",
                "zone_key": self.zone_key,
                "zone_name": self.zone_name,
                "zone_port": self.zone_port,
                "zone_user": self.admin_username
            }
        }

        if self.irods_version < (4, 90, 0):
            # Remove iRODS 5 configuration.
            json_input["server_config"].pop("client_server_policy", None)
            json_input["server_config"].pop("connection_pool_refresh_time_in_seconds", None)
            json_input["server_config"].pop("encryption", None)
            json_input["server_config"].pop("graceful_shutdown_timeout_in_seconds", None)
            json_input["server_config"].pop("host", None)
            json_input["server_config"]["log_level"].pop("genquery1", None)

            # Add iRODS 4.3 configuration.
            json_input["service_account_environment"].update({
                "irods_client_server_negotiation": "request_server_negotiation",
                "irods_server_control_plane_encryption_algorithm": "AES-256-CBC",
                "irods_server_control_plane_encryption_num_hash_rounds": 16,
                "irods_server_control_plane_key": "32_byte_server_control_plane_key",
                "irods_server_control_plane_port": 1248,
                "irods_server_control_plane_timeout_milliseconds": 10000,
                "schema_version": "v4"
            })
            json_input["server_config"]["advanced_settings"]["agent_factory_watcher_sleep_time_in_seconds"] = 5
            json_input["server_config"]["advanced_settings"]["default_log_rotation_in_days"] = 5
            json_input["server_config"]["client_api_allowlist_policy"] = "enforce"
            json_input["server_config"]["plugin_configuration"]["database"] = {
                self.database_technology: {
                    "db_host": self.database_server_hostname,
                    "db_name": self.database_name,
                    "db_odbc_driver": self.odbc_driver,
                    "db_password": self.database_password,
                    "db_port": self.database_server_port,
                    "db_username": self.database_username
                }
            }
            json_input["server_config"].update({
                "schema_validation_base_uri": "file:///var/lib/irods/configuration_schemas",
                "schema_version": "v4",
                "server_control_plane_encryption_algorithm": "AES-256-CBC",
                "server_control_plane_encryption_num_hash_rounds": 16,
                "server_control_plane_key": "32_byte_server_control_plane_key",
                "server_control_plane_port": 1248,
                "server_control_plane_timeout_milliseconds": 10000
            })

        return json.dumps(json_input, sort_keys=True, indent=4)

    def build(self):
        """Build the string for the setup script input.

        Depending on the way the inputs were provided, either an iRODS catalog service provider
        or a catalog service consumer will be set up and the resulting input string will be
        returned.
        """
        if self.do_unattended_install:
            build_for_role = {
                'provider': self.build_unattended_install_input_for_catalog_provider,
                'consumer': self.build_unattended_install_input_for_catalog_consumer
            }
        else:
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

        # TODO: Remove multiple attempts when a more appropriate solution is found
        MAX_NUMBER_OF_ATTEMPTS = 3
        num_attempts = 1

        logging.debug("[{}] Attempting startup of rsyslogd".format(container.name))

        while num_attempts <= MAX_NUMBER_OF_ATTEMPTS:
            logging.debug("[{}] running startup attempt [#{}]".format(container.name, num_attempts))
            ec = execute.execute_command(container, rsyslog_bin_path)
            logging.debug("[{}] startup attempt [#{}] {status}.".format(container.name, num_attempts, status="succeeded" if ec == 0 else "failed"))

            logging.debug("[{}] checking to see if rsyslogd started up in the background.".format(container.name))
            is_alive = execute.execute_command(container, f'pgrep {os.path.basename(rsyslog_bin_path)}') == 0
            logging.debug("[{}] result of checking if rsyslogd is running: [{}]".format(container.name, is_alive))

            # If we started an instance successfully, or it's restarted by another mechanism, we're satisfied
            if ec == 0 or is_alive:
                break

            num_attempts += 1

        # Ensure we don't end up in a loop of failed start attempts, and that we log the failure
        if num_attempts > MAX_NUMBER_OF_ATTEMPTS:
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
        :programname,startswith,\\"irodsAgent\\" /var/log/irods/irods.log;irods_format
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
    cmd = "python3 -c 'from scripts.irods.controller import IrodsController; IrodsController().stop()'"
    return execute.execute_command(container, cmd, user='irods', workdir=context.irods_home())


def restart_irods(container):
    cmd = "python3 -c 'from scripts.irods.controller import IrodsController; IrodsController().restart()'"
    return execute.execute_command(container, cmd, user='irods', workdir=context.irods_home())


def setup_irods_server(container, setup_input, **kwargs):
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

    try:
        if stop_irods(container) != 0:
            logging.debug(f'[{container.name}] failed to stop iRODS server before setup')
    except Exception as e:
        error_msg = f'[{container.name}] failed to stop iRODS server before setup: {str(e)}'
        if "unable to find user irods" in str(e):
            # If the user didn't exist at this point then the service probably wasn't started.
           logging.debug(error_msg)
        else:
           logging.error(error_msg)
           raise e

    # Base64 encoding the input file allows the testing environment to transfer it via the
    # shell without any problems.
    import base64
    import shlex
    b64 = base64.b64encode(setup_input.encode('utf-8')).decode('ascii')
    ec = execute.execute_command(container, f"bash -lc 'printf %s {shlex.quote(b64)} | base64 -d > /input'")
    if ec != 0:
        raise RuntimeError('failed to create setup script input file [{}]'.format(container.name))

    execute.execute_command(container, 'cat /input')

    path_to_setup_script = os.path.join(context.irods_home(), 'scripts', 'setup_irods.py')
    if kwargs.get('do_unattended_install', False):
        run_setup_script = 'bash -c \'{} {} --json_configuration_file /input\''.format(
            container_info.python(container), path_to_setup_script)
    else:
        run_setup_script = 'bash -c \'{} {} < /input\''.format(
            container_info.python(container), path_to_setup_script)
    ec = execute.execute_command(container, run_setup_script)
    if ec != 0:
        raise RuntimeError('failed to set up iRODS server [{}]'.format(container.name))

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

    logging.debug('database name: [%s]', ctx.database_name())
    db_technology, db_odbc_driver = {
        'postgres': ('postgres', 'PostgreSQL ANSI'),
        'mysql': ('mysql', 'MySQL ANSI'),
        'mariadb': ('mysql', 'MySQL ANSI')
    }[ctx.database_name()]
    logging.debug('database technology: [%s], derived odbc driver: [%s]', db_technology, db_odbc_driver)

    setup_input = (setup_input_builder()
        .setup(irods_version=irods_config.get_irods_version(csp_container),
               catalog_service_role='provider',
               host=context.container_hostname(csp_container),
               database_technology=db_technology,
               odbc_driver=odbc_driver or db_odbc_driver, # Ignored for prompt-based installs.
               database_server_hostname=context.container_hostname(db_container),
               database_server_port=database_setup.database_server_port(ctx.database()),
               **kwargs)
        .build()
    )

    logging.debug('input to setup script [{}]'.format(setup_input))

    logging.warning('setting up iRODS catalog provider [{}]'.format(csp_container.name))

    setup_irods_server(csp_container,
                       setup_input,
                       do_unattended_install=kwargs.get('do_unattended_install', False))


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

    csc_container_hostname = context.container_hostname(csc_container)

    # Mirrors how setup_irods.py in irods/irods generates the default resource name
    # for catalog service consumer servers.
    resource_name = csc_container_hostname.split('.')[0] + 'Resource'

    setup_input = (setup_input_builder()
        .setup(irods_version=irods_config.get_irods_version(csc_container),
               catalog_service_role='consumer',
               host=csc_container_hostname,
               resource_name=resource_name,
               catalog_service_provider_host=context.container_hostname(csp_container),
               **kwargs)
        .build()
    )

    logging.debug('input to setup script [{}]'.format(setup_input))

    logging.warning('setting up iRODS catalog consumer [{}]'.format(csc_container.name))

    setup_irods_server(csc_container,
                       setup_input,
                       do_unattended_install=kwargs.get('do_unattended_install', False))


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

    if rc != 0:
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
                      odbc_driver=None,
                      **kwargs):
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
                            **kwargs,
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

    if rc != 0:
        raise RuntimeError('failed to set up one or more iRODS Zones, ec=[{}]'.format(rc))


def make_negotiation_key(prefix=''):
    """Generate a 32-byte negotiation key with an optional prefix.

    The generated key will be 32 bytes in length. If a longer string is passed in, it will be
    truncated to 32 bytes. If the string is shorter than 32 bytes, the remaining space will be
    filled by underscores.

    Arguments:
    prefix -- optional prefix to use to make the key unique
    """
    negotation_key_size_in_bytes = 32

    if len(prefix) > negotation_key_size_in_bytes:
        return prefix[:negotiation_key_size_in_bytes]

    filler = '_' * negotation_key_size_in_bytes
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
