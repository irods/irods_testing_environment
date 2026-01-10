# grown-up modules
import docker
import logging
import time

# local modules
from . import context
from . import execute

def database_server_port(database_image):
    """Return the default port for the database server indicated by `database_image`.

    Arguments:
    database_image -- repo:tag for the docker image of the database server
    """
    db = context.image_repo(database_image)

    if 'postgres' in db:
        return 5432
    elif 'mysql' in db or 'mariadb' in db:
        return 3306
    else:
        raise NotImplementedError('database not supported [{}]'.format(database_image))


class database_setup_strategy(object):
    """'Base class' for strategies for database setup.

    This class should not be instantiated directly.
    """
    def create_database(self, name, force_recreate=False):
        """Create a database.

        This method must be overridden.

        Arguments:
        name -- name of the database to create
        force_recreate -- if True, drops any database by the specified name before creating
        """
        raise NotImplementedError('method not implemented for database strategy')

    def create_user(self, username, password, force_recreate=False):
        """Create a user for the database.

        This method must be overridden.

        Arguments:
        username -- name of the user to create
        password -- password for the new user
        force_recreate -- if True, drops any user by the specified username before creating
        """
        raise NotImplementedError('method not implemented for database strategy')

    def grant_privileges(self, database, username):
        """Grant all privileges on database to user called `username`.

        This method must be overridden.

        Arguments:
        database -- name of the database on which privileges are being granted
        username -- name of the user for whom privileges are being granted
        """
        raise NotImplementedError('method not implemented for database strategy')

    def drop_database(self, name):
        """Drop a database called `name`.

        This method must be overridden.

        Arguments:
        name -- name of the database to drop
        """
        raise NotImplementedError('method not implemented for database strategy')

    def drop_user(self, username):
        """Drop a user named `username`.

        This method must be overridden.

        Arguments:
        username -- name of the user to drop
        """
        raise NotImplementedError('method not implemented for database strategy')

    def list_databases(self):
        """List databases.

        This method must be overridden.
        """
        raise NotImplementedError('method not implemented for database strategy')


class postgres_database_setup_strategy(database_setup_strategy):
    """Database setup strategy for postgres"""
    def __init__(self, container=None, root_password=None, port=None):
        """Construct a postgres_database_setup_strategy.

        Arguments:
        container -- docker.client.container running the database
        root_password -- password for the root database user
        port -- port on which the postgres server is listening (default: 5432)
        """
        self.container = container
        self.root_password = root_password if root_password else 'testpassword'
        self.port = port if port else 5432

    def execute_psql_command(self, psql_cmd):
        """Execute a psql command as the postgres user.

        Arguments:
        psql_cmd -- command to be passed to psql via --command
        """
        cmd = 'psql --port {0} --command \"{1}\"'.format(self.port, psql_cmd)
        return execute.execute_command(self.container, cmd, user='postgres')

    def connect_to_database(self, name='postgres', as_user='postgres'):
        """Connect to database named `name` as user `as_user`.

        Arguments:
        name -- name of the database to check
        as_user -- name of the user/role connecting to the database
        """
        return self.execute_psql_command('\c \'{}\' \'{}\';'.format(name, as_user))

    def database_exists(self, name):
        """Confirm existence of a database by attempting to connect to it.

        Arguments:
        name -- name of the database to check
        """
        return self.connect_to_database(name=name) == 0

    def user_exists(self, username):
        """Confirm existence of a user/role by attempting to connect to database as `username`.

        Arguments:
        username -- name of the user/role to check
        """
        return self.connect_to_database(as_user=username) == 0

    def create_database(self, name, force_recreate=False):
        """Create a database.

        Arguments:
        name -- name of the database to create
        force_recreate -- if True, drops any database by the specified name before creating
        """
        if force_recreate: self.drop_database(name)

        return 0 if self.database_exists(name) \
                 else self.execute_psql_command('create database \\\"{}\\\";'.format(name))

    def create_user(self, username, password, force_recreate=False):
        """Create a user for the database.

        Arguments:
        username -- name of the user to create
        password -- password for the new user
        force_recreate -- if True, drops any user by the specified username before creating
        """
        if force_recreate: self.drop_user(username)

        return 0 if self.user_exists(username) \
                 else self.execute_psql_command('create user {0} with password \'{1}\';'
                                                .format(username, password))

    def grant_privileges(self, database, username):
        """Grant all privileges on database to user called `username`.

        Arguments:
        database -- name of the database on which privileges are being granted
        username -- name of the user for whom privileges are being granted
        """
        ec = self.execute_psql_command('grant all privileges on database \\\"{0}\\\" to {1};'
            .format(database, username))
        if ec is not 0:
            return ec
        return self.execute_psql_command('alter database \\\"{0}\\\" owner to {1};'
            .format(database, username))

    def drop_database(self, name):
        """Drop a database called `name`.

        Arguments:
        name -- name of the database to drop
        """
        return self.execute_psql_command('drop database \\\"{}\\\";'.format(name))

    def drop_user(self, username):
        """Drop a user named `username`.

        Arguments:
        username -- name of the user to drop
        """
        return self.execute_psql_command('drop user {};'.format(username))

    def list_databases(self):
        """List databases."""
        return self.execute_psql_command('\l')


class mysql_database_setup_strategy(database_setup_strategy):
    """Database setup strategy for mysql"""
    def __init__(self, container=None, root_password=None, port=None, db_exec=None):
        """Construct a mysql_database_setup_strategy.

        Arguments:
        container -- docker.client.container running the database
        root_password -- password for the root database user
        database_port -- port on which the postgres server is listening (default: 3306)
        db_exec -- name of the standard command-line client executable 
        """
        self.container = container
        self.root_password = root_password if root_password else 'testpassword'
        self.port = port if port else 3306
        self.db_exec = db_exec if db_exec else 'mysql'
        # TODO: 'irods'@'%' is generated by the docker entrypoint for mysql container...
        # should be 'irods'@'localhost', but that doesn't work right now
        self.host = '%'

    def execute_mysql_command(self, mysql_cmd, user='root', password='testpassword'):
        """Execute a mysql command as the postgres user.

        Arguments:
        mysql_cmd -- the command to be passed to mysql via --execute
        """
        return execute.execute_command(self.container,
            '{0} --host 127.0.0.1 --port {1} --user {2} --password={3} --execute \"{4}\"'
            .format(self.db_exec, self.port, user, password, mysql_cmd))

    def connect_to_database(self,
                            name='information_schema',
                            as_user='root',
                            with_password='testpassword'):
        """Connect to database named `name` as user `as_user`.

        Arguments:
        name -- name of the database to check
        as_user -- name of the user/role connecting to the database
        """

        logging.debug('checking if database is accepting connection ...')

        # Make sure the database is ready for connections.
        while self.execute_mysql_command('SHOW DATABASES;') != 0:
            logging.debug('database is not accepting connections yet. retrying in 5 seconds ...')
            time.sleep(5)

        logging.debug('database is ready!')

        return self.execute_mysql_command('\\r \'{}\''.format(name),
                                          user=as_user,
                                          password=with_password)

    def database_exists(self, name):
        """Confirm existence of a database by attempting to connect to it.

        Arguments:
        name -- name of the database to check
        """
        return self.connect_to_database(name=name) == 0

    def user_exists(self, username, password='testpassword'):
        """Confirm existence of a user/role by attempting to connect to database as `username`.

        Arguments:
        username -- name of the user/role to check
        """
        return self.connect_to_database(as_user=username, with_password=password) == 0

    def create_database(self, name, force_recreate=False):
        """Create a database.

        Arguments:
        name -- name of the database to create
        force_recreate -- if True, drops any database by the specified name before creating
        """
        if force_recreate: self.drop_database(name)

        return 0 if self.database_exists(name) \
                 else self.execute_mysql_command('CREATE DATABASE {};'.format(name))

    def create_user(self, username, password, force_recreate=False):
        """Create a user for the database.

        Arguments:
        username -- name of the user to create
        password -- password for the new user
        force_recreate -- if True, drops any user by the specified username before creating
        """
        user = '\'{}\'@\'{}\''.format(username, self.host)

        if force_recreate: self.drop_user(user)

        return 0 if self.user_exists(username, password) \
                 else self.execute_mysql_command(
                    'CREATE USER {} IDENTIFIED BY \'{}\';'
                    .format(user, password))

    def grant_privileges(self, database, username):
        """Grant all privileges on database to user called `username`.

        Arguments:
        database -- name of the database on which privileges are being granted
        username -- name of the user for whom privileges are being granted
        """
        user = '\'{}\'@\'{}\''.format(username, self.host)

        return self.execute_mysql_command('GRANT ALL ON {}.* to {};'.format(database, user))

    def drop_database(self, name):
        """Drop a database called `name`.

        Arguments:
        name -- name of the database to drop
        """
        return self.execute_mysql_command('DROP DATABASE {};'.format(name))

    def drop_user(self, username):
        """Drop a user named `username`.

        Arguments:
        username -- name of the user to drop
        """
        user = '\'{}\'@\'{}\''.format(username, self.host)

        return self.execute_mysql_command('DROP USER {};'.format(user))

    def list_databases(self):
        """List databases."""
        return self.execute_mysql_command('SHOW DATABASES;')


class mariadb_database_setup_strategy(mysql_database_setup_strategy):
    """Database setup strategy for mariadb"""
    def __init__(self, container=None, root_password=None, port=None, db_exec=None):
        """Construct a mysql_database_setup_strategy.

        Arguments:
        container -- docker.client.container running the database
        root_password -- password for the root database user
        database_port -- port on which the postgres server is listening (default: 3306)
        db_exec -- name of the standard command-line client executable 
        """
        db_exec = db_exec if db_exec else 'mariadb'
        super(mariadb_database_setup_strategy, self).__init__(container, root_password, port, db_exec)

    def execute_mariadb_command(self, mariadb_cmd, user='root', password='testpassword'):
        """Execute a mariadb command.

        Arguments:
        mariadb_cmd -- the command to be passed to mariadb via --execute
        """
        return self.execute_mysql_command(mariadb_cmd, root, password)


def make_strategy(database_image, container=None, database_port=None, root_password=None):
    """Make a database setup strategy for the given database type.

    Arguments:
    database_image -- repo:tag for the docker image of the database server
    container -- docker container running the database service
    database_port -- port on which the database service is listening
    database_root_password -- password the database root user
    """
    strat_name = context.image_repo(database_image) + '_database_setup_strategy'

    return eval(strat_name)(container, database_port, root_password)

def setup_catalog(ctx,
                  force_recreate=False,
                  database_port=None,
                  service_instance=1,
                  database_name='ICAT',
                  database_user='irods',
                  database_password='testpassword',
                  root_password=None):
    """Set up the iRODS catalog on the specified database service.

    Arguments:
    force_recreate -- if True, drops any database and user by the specified names
    database_port -- the port on which the database service is listening
    service_instance -- service instance number for the database service being targeted
    database_name -- name of the iRODS database (for testing, this should be 'ICAT')
    database_user -- name of the iRODS database user (for testing, this should be 'irods')
    database_password -- password for the iRODS database user (for testing this should be
                         'testpassword')
    root_password -- password for the root database user
    """
    db_container = ctx.docker_client.containers.get(
        context.irods_catalog_database_container(ctx.compose_project.name, service_instance))

    logging.warning('setting up catalog [{}]'.format(db_container.name))

    strat = make_strategy(ctx.database(), db_container, database_port, root_password)

    ec = strat.create_database(database_name, force_recreate)
    if ec is not 0:
        raise RuntimeError('failed to create database [{}]'.format(database_name))

    ec = strat.create_user(database_user, database_password, force_recreate)
    if ec is not 0:
        raise RuntimeError('failed to create user [{}]'.format(database_user))

    ec = strat.grant_privileges(database_name, database_user)
    if ec is not 0:
        raise RuntimeError('failed to grant privileges to user [{0}] on database [{1}]'.format(database_user, database_name))

    strat.list_databases()

def wait_for_database_service(ctx,
                              database_service_instance=1,
                              seconds_between_retries=1,
                              retry_count=60):
    """Attempt to connect to the database service, looping until successful.

    Arguments:
    ctx -- context object which contains information about the Docker environment
    database_service_instance -- the service instance number of the container running the
                                 database server
    seconds_between_retries -- seconds to sleep between retries to connect
    retry_count -- number of times to retry (note: must be a non-negative integer)
    """
    from . import container_info

    if retry_count < 0:
        raise ValueError('retry_count must be a non-negative integer')

    irods_container = ctx.docker_client.containers.get(
        context.irods_catalog_provider_container(ctx.compose_project.name))

    db_container = ctx.docker_client.containers.get(
        context.irods_catalog_database_container(ctx.compose_project.name, database_service_instance))
    db_address = context.container_ip(db_container, ctx.compose_project.name + '_default')
    db_port = database_server_port(ctx.database())

    logging.info(f'waiting for catalog to be ready [{db_container.name}]')

    retries = -1
    while retries < retry_count:
        logging.debug(
            f'[{irods_container.name}] trying database on [{db_container.name}] ip:[{db_address}] port:[{db_port}]')

        socket_cmd = str('import socket; '
            's = socket.socket(socket.AF_INET, socket.SOCK_STREAM); '
            f'ec = s.connect_ex((\'{db_address}\', {db_port})); '
            's.close(); print(ec); exit(ec)'
        )

        cmd = ' '.join([container_info.python(irods_container), '-c', f'"{socket_cmd}"'])
        if execute.execute_command(irods_container, cmd) == 0:
            logging.debug(
                f'[{irods_container.name}] database service ready on [{db_container.name}]')
            return

        retries = retries + 1
        time.sleep(seconds_between_retries)

    raise RuntimeError(f'maximum retries reached attempting to connect to database [{db_container.name}]')
