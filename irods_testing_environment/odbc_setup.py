# grown-up modules
import logging
import os
import textwrap

# local modules
from . import archive
from . import context
from . import execute

# iRODS currently has problems with the MariaDB ODBC driver.
# Flip this bool to switch which ODBC driver is used for MariaDB projects.
mariadb_use_mysql_odbc_driver = True

def make_postgres_odbcinst_ini(csp_container):
    """Generate content for the /etc/odbcinst.ini configuration file used by postgres.
    Most of the time this is not needed.

    Arguments:
    csp_container -- container running iRODS catalog service provider using the ODBC driver
    """
    odbcinst_ini_path = os.path.join('/etc', 'odbcinst.ini')

    logging.debug('configuring odbcinst.ini with PostgreSQL drivers')
    odbcinst_ini_contents = textwrap.dedent("""\
        [PostgreSQL ANSI]
        Description     = ODBC for PostgreSQL
        Driver          = /usr/lib/psqlodbcw.so
        Setup           = /usr/lib/libodbcpsqlS.so
        Driver64        = /usr/lib64/psqlodbcw.so
        Setup64         = /usr/lib64/libodbcpsqlS.so
        FileUsage       = 1
        """)

    cmd = 'bash -c \'echo "{0}" > {1}\''.format(odbcinst_ini_contents, odbcinst_ini_path)
    ec = execute.execute_command(csp_container, cmd)
    if ec != 0:
        raise RuntimeError('failed to populate odbcinst.ini [ec=[{0}], container=[{1}]]'
            .format(ec, csp_container))

    execute.execute_command(csp_container, 'cat {}'.format(odbcinst_ini_path))

def configure_postgres_odbc_driver(csp_container, odbc_driver):
    """Configure ODBC driver for postgres.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    logging.debug('no ODBC driver setup required for postgres [{}]'.format(csp_container))

def configure_odbc_driver_ubuntu_2004_postgres_14(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 14 on ubuntu 20.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_ubuntu_2004_postgres_16(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 16 on ubuntu 20.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_ubuntu_2204_postgres_14(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 14 on ubuntu 22.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_ubuntu_2204_postgres_16(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 16 on ubuntu 22.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_ubuntu_2404_postgres_14(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 14 on ubuntu 24.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_ubuntu_2404_postgres_16(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 16 on ubuntu 24.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_ubuntu_2404_postgres_17(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 17 on ubuntu 24.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_debian_11_postgres_14(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 14 on debian 11.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_debian_11_postgres_16(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 16 on debian 11.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_debian_12_postgres_14(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 14 on debian 12.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_debian_12_postgres_16(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 16 on debian 12.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_debian_12_postgres_17(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 17 on debian 12.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_debian_13_postgres_16(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 16 on debian 13.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_debian_13_postgres_17(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 17 on debian 13.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_almalinux_8_postgres_14(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 14 on almalinux 8.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_almalinux_8_postgres_16(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 16 on almalinux 8.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_8_postgres_14(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 14 on rockylinux 8.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_8_postgres_16(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 16 on rockylinux 8.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_almalinux_9_postgres_14(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 14 on almalinux 9.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_almalinux_9_postgres_16(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 16 on almalinux 9.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_almalinux_9_postgres_17(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 17 on almalinux 9.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_9_postgres_14(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 14 on rockylinux 9.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_9_postgres_16(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 16 on rockylinux 9.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_9_postgres_17(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 17 on rockylinux 9.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_el10_postgres(csp_container, odbc_driver):
    """Configure ODBC driver for postgres on EL10.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    """
    make_postgres_odbcinst_ini(csp_container)

def configure_odbc_driver_almalinux_10_postgres_16(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 16 on almalinux 10.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el10_postgres(csp_container, odbc_driver)

def configure_odbc_driver_almalinux_10_postgres_17(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 17 on almalinux 10.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el10_postgres(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_10_postgres_16(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 16 on rockylinux 10.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el10_postgres(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_10_postgres_17(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 17 on rockylinux 10.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el10_postgres(csp_container, odbc_driver)

def make_mysql_odbcinst_ini(csp_container, container_odbc_driver_dir):
    """Generate content for the /etc/odbcinst.ini configuration file used by mysql.

    Arguments:
    csp_container -- container running iRODS catalog service provider using the ODBC driver
    container_odbc_driver_dir -- path in `csp_container` containing the ODBC driver directory
    """
    odbcinst_ini_path = os.path.join('/etc', 'odbcinst.ini')

    # This is the same for both 8.0 and 8.4.
    logging.debug('configuring odbcinst.ini with MySQL 8.x drivers')
    odbcinst_ini_contents = textwrap.dedent("""\
        [MySQL ANSI]
        Description = MySQL ODBC 8.0 ANSI Driver
        Driver = {0}/lib/libmyodbc8a.so

        [MySQL Unicode]
        Description = MySQL ODBC 8.0 Unicode Driver
        Driver = {0}/lib/libmyodbc8w.so""".format(container_odbc_driver_dir))

    cmd = 'bash -c \'echo "{0}" > {1}\''.format(odbcinst_ini_contents, odbcinst_ini_path)
    ec = execute.execute_command(csp_container, cmd)
    if ec != 0:
        raise RuntimeError('failed to populate odbcinst.ini [ec=[{0}], container=[{1}]]'
            .format(ec, csp_container))

    execute.execute_command(csp_container, 'cat {}'.format(odbcinst_ini_path))

def configure_mysql_odbc_driver(csp_container, odbc_driver, extension='tar.gz'):
    """Configure ODBC driver for mysql and return the ODBC driver path.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    extension -- file extension for the archive file
    """
    if not os.path.exists(odbc_driver):
        raise RuntimeError('indicated ODBC driver does not exist [{}]'.format(odbc_driver))

    logging.info('looking for odbc driver [{}]'.format(odbc_driver))

    container_odbc_driver_dir = archive.copy_archive_to_container(csp_container,
                                                                  odbc_driver,
                                                                  extension=extension)

    execute.execute_command(csp_container, 'ls -l {}'.format(container_odbc_driver_dir))

    make_mysql_odbcinst_ini(csp_container, container_odbc_driver_dir)

    return container_odbc_driver_dir

def download_mysql_odbc_driver(url, destination=None, always_download=False):
    """Downloads the file indicated by `url` and returns the path to the file.

    Arguments:
    url -- URL of the file to download
    destination -- destination path on local filesystem for the file to be downloaded
    """
    import shutil
    import tempfile
    import urllib.request

    if not destination:
        from urllib.parse import urlparse
        destination = os.path.join('/tmp', os.path.basename(urlparse(url).path))

    destination = os.path.abspath(destination)

    if not always_download and os.path.exists(destination):
        logging.info('destination mysql odbc already exists, not downloading [{}]'
                     .format(destination))
        return destination

    logging.info('downloading [{}] to [{}]'.format(url, destination))

    with urllib.request.urlopen(url) as r:
        with open(destination, 'w+b') as f:
            shutil.copyfileobj(r, f)

    return destination

def configure_odbc_driver_mysql_80(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    if not odbc_driver:
        odbc_driver = download_mysql_odbc_driver(
            'https://dev.mysql.com/get/Downloads/Connector-ODBC/8.0/mysql-connector-odbc-8.0.33-linux-glibc2.28-x86-64bit.tar.gz')

    configure_mysql_odbc_driver(csp_container, os.path.abspath(odbc_driver))

def configure_odbc_driver_mysql_84(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.4.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    if not odbc_driver:
        odbc_driver = download_mysql_odbc_driver(
            'https://dev.mysql.com/get/Downloads/Connector-ODBC/8.4/mysql-connector-odbc-8.4.0-linux-glibc2.28-x86-64bit.tar.gz')

    configure_mysql_odbc_driver(csp_container, os.path.abspath(odbc_driver))

def configure_odbc_driver_ubuntu_2004_mysql_80(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on ubuntu 20.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_80(csp_container, odbc_driver)

def configure_odbc_driver_ubuntu_2204_mysql_80(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on ubuntu 22.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_80(csp_container, odbc_driver)

def configure_odbc_driver_ubuntu_2204_mysql_84(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.4 on ubuntu 22.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_84(csp_container, odbc_driver)

def configure_odbc_driver_ubuntu_2404_mysql_80(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on ubuntu 24.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_80(csp_container, odbc_driver)

def configure_odbc_driver_ubuntu_2404_mysql_84(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.4 on ubuntu 24.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_84(csp_container, odbc_driver)

def configure_odbc_driver_debian_11_mysql_80(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on debian 11.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_80(csp_container, odbc_driver)

def configure_odbc_driver_debian_12_mysql_80(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on debian 12.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_80(csp_container, odbc_driver)

def configure_odbc_driver_debian_12_mysql_84(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.4 on debian 12.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_84(csp_container, odbc_driver)

def configure_odbc_driver_debian_13_mysql_80(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on debian 13.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_80(csp_container, odbc_driver)

def configure_odbc_driver_debian_13_mysql_84(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.4 on debian 13.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_84(csp_container, odbc_driver)

def configure_odbc_driver_almalinux_8_mysql_80(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on almalinux 8.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_80(csp_container, odbc_driver)

def configure_odbc_driver_almalinux_8_mysql_84(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.4 on almalinux 8.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_84(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_8_mysql_80(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on rockylinux 8.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_80(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_8_mysql_84(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.4 on rockylinux 8.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_84(csp_container, odbc_driver)

def configure_odbc_driver_almalinux_9_mysql_80(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on almalinux 9.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_80(csp_container, odbc_driver)

def configure_odbc_driver_almalinux_9_mysql_84(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.4 on almalinux 9.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_84(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_9_mysql_80(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on rockylinux 9.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_80(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_9_mysql_84(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.4 on rockylinux 9.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_84(csp_container, odbc_driver)

def configure_odbc_driver_almalinux_10_mysql_80(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on almalinux 10.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_80(csp_container, odbc_driver)

def configure_odbc_driver_almalinux_10_mysql_84(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.4 on almalinux 10.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_84(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_10_mysql_80(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on rockylinux 10.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_80(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_10_mysql_84(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.4 on rockylinux 10.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_mysql_84(csp_container, odbc_driver)

def make_mariadb_odbcinst_ini(csp_container, container_odbc_lib_dir):
    """Generate content for the /etc/odbcinst.ini configuration file used by mariadb.

    Arguments:
    csp_container -- container running iRODS catalog service provider using the ODBC driver
    container_odbc_lib_dir -- path in `csp_container` containing the ODBC driver library
    """
    odbcinst_ini_path = os.path.join('/etc', 'odbcinst.ini')

    odbcinst_ini_contents = textwrap.dedent("""\
        [MariaDB]
        Description = MariaDB ODBC Connector
        Driver      = {0}/libmaodbc.so
        Threading   = 0
        """.format(container_odbc_lib_dir))

    cmd = 'bash -c \'echo "{0}" > {1}\''.format(odbcinst_ini_contents, odbcinst_ini_path)
    ec = execute.execute_command(csp_container, cmd)
    if ec != 0:
        raise RuntimeError('failed to populate odbcinst.ini [ec=[{0}], container=[{1}]]'
            .format(ec, csp_container))

    execute.execute_command(csp_container, 'cat {}'.format(odbcinst_ini_path))

def configure_mariadb_odbc_driver_apt(csp_container, odbc_driver, package_url):
    """Configure ODBC driver package for mariadb (via apt)

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    package_url -- location of ODBC driver package to download if odbc_driver is not provided
    """
    if mariadb_use_mysql_odbc_driver:
        configure_odbc_driver_mysql_80(csp_container, odbc_driver)
        return

    if not odbc_driver:
        odbc_driver = download_mysql_odbc_driver(package_url)
    odbc_driver = os.path.abspath(odbc_driver)

    odbc_driver_archive = archive.create_archive([odbc_driver])
    archive.copy_archive_to_container(csp_container, odbc_driver_archive)

    execute.execute_command(csp_container, 'apt-get update')
    execute.execute_command(csp_container, 'apt-get install {}'.format(odbc_driver))

    make_mariadb_odbcinst_ini(csp_container, '/usr/lib/x86_64-linux-gnu')

def configure_mariadb_odbc_driver_dnf(csp_container, odbc_driver, package_url):
    """Configure ODBC driver package for mariadb (via yum)

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    package_url -- location of ODBC driver package to download if odbc_driver is not provided
    """
    if mariadb_use_mysql_odbc_driver:
        configure_odbc_driver_mysql_80(csp_container, odbc_driver)
        return

    if not odbc_driver:
        odbc_driver = download_mysql_odbc_driver(package_url)
    odbc_driver = os.path.abspath(odbc_driver)

    odbc_driver_archive = archive.create_archive([odbc_driver])
    archive.copy_archive_to_container(csp_container, odbc_driver_archive)

    execute.execute_command(csp_container, 'dnf install -y {}'.format(odbc_driver))

    make_mariadb_odbcinst_ini(csp_container, '/usr/lib64')

def configure_odbc_driver_ubuntu_2004_mariadb(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb on ubuntu 20.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_mariadb_odbc_driver_apt(
        csp_container,
        odbc_driver,
        'https://downloads.mariadb.com/Connectors/odbc/connector-odbc-3.2.2/mariadb-connector-odbc-3.2.2-ubu2004-amd64.deb')

def configure_odbc_driver_ubuntu_2004_mariadb_106(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 10.6 on ubuntu 20.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_ubuntu_2004_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_ubuntu_2004_mariadb_1011(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 10.11 on ubuntu 20.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_ubuntu_2004_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_ubuntu_2204_mariadb(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb on ubuntu 22.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_mariadb_odbc_driver_apt(
        csp_container,
        odbc_driver,
        'https://downloads.mariadb.com/Connectors/odbc/connector-odbc-3.2.2/mariadb-connector-odbc-3.2.2-ubu2204-amd64.deb')

def configure_odbc_driver_ubuntu_2204_mariadb_106(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 10.6 on ubuntu 22.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_ubuntu_2204_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_ubuntu_2204_mariadb_1011(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 10.11 on ubuntu 22.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_ubuntu_2204_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_ubuntu_2204_mariadb_114(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 11.4 on ubuntu 22.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_ubuntu_2204_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_ubuntu_2404_mariadb(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb on ubuntu 24.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_mariadb_odbc_driver_apt(
        csp_container,
        odbc_driver,
        'https://downloads.mariadb.com/Connectors/odbc/connector-odbc-3.2.6/mariadb-connector-odbc_3.2.6-1+maria~noble_amd64.deb')

def configure_odbc_driver_ubuntu_2404_mariadb_1011(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 10.11 on ubuntu 24.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_ubuntu_2404_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_ubuntu_2404_mariadb_114(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 11.4 on ubuntu 24.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_ubuntu_2404_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_ubuntu_2404_mariadb_118(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 11.8 on ubuntu 24.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_ubuntu_2404_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_debian_11_mariadb(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb on debian 11.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_mariadb_odbc_driver_apt(
        csp_container,
        odbc_driver,
        'https://downloads.mariadb.com/Connectors/odbc/connector-odbc-3.2.2/mariadb-connector-odbc-3.2.2-deb11-amd64.deb')

def configure_odbc_driver_debian_11_mariadb_106(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 10.6 debian 11.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_debian_11_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_debian_11_mariadb_1011(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 10.11 debian 11.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_debian_11_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_debian_12_mariadb(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb on debian 12.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_mariadb_odbc_driver_apt(
        csp_container,
        odbc_driver,
        'https://downloads.mariadb.com/Connectors/odbc/connector-odbc-3.2.6/mariadb-connector-odbc_3.2.6-1+maria~bookworm_amd64.deb')

def configure_odbc_driver_debian_12_mariadb_1011(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 10.11 debian 12.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_debian_12_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_debian_12_mariadb_114(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 11.4 debian 12.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_debian_12_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_debian_12_mariadb_118(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 11.8 debian 12.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_debian_12_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_debian_13_mariadb(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb on debian 13.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_mariadb_odbc_driver_apt(
        csp_container,
        odbc_driver,
        # Package is for Debian 12
        'https://downloads.mariadb.com/Connectors/odbc/connector-odbc-3.2.6/mariadb-connector-odbc_3.2.6-1+maria~bookworm_amd64.deb')

def configure_odbc_driver_debian_13_mariadb_114(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 11.4 debian 13.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_debian_13_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_debian_13_mariadb_118(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 11.8 debian 13.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_debian_13_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_el_8_mariadb(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb on EL 8.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_mariadb_odbc_driver_dnf(
        csp_container,
        odbc_driver,
        'https://downloads.mariadb.com/Connectors/odbc/connector-odbc-3.2.2/mariadb-connector-odbc-3.2.2-rhel8-amd64.rpm')

def configure_odbc_driver_almalinux_8_mariadb_106(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 10.6 almalinux 8.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el_8_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_almalinux_8_mariadb_1011(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 10.11 almalinux 8.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el_8_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_almalinux_8_mariadb_114(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 11.4 almalinux 8.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el_8_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_8_mariadb_106(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 10.6 rockylinux 8.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el_8_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_8_mariadb_1011(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 10.11 rockylinux 8.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el_8_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_8_mariadb_114(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 11.4 rockylinux 8.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el_8_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_el_9_mariadb(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb on EL 9.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_mariadb_odbc_driver_dnf(
        csp_container,
        odbc_driver,
        'https://downloads.mariadb.com/Connectors/odbc/connector-odbc-3.2.6/mariadb-connector-odbc-3.2.6-1.el9.x86_64.rpm')

def configure_odbc_driver_almalinux_9_mariadb_1011(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 10.11 almalinux 9.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el_9_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_almalinux_9_mariadb_114(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 11.4 almalinux 9.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el_9_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_almalinux_9_mariadb_118(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 11.8 almalinux 9.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el_9_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_9_mariadb_1011(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 10.11 rockylinux 9.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el_9_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_9_mariadb_114(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 11.4 rockylinux 9.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el_9_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_9_mariadb_118(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 11.8 rockylinux 9.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el_9_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_el_10_mariadb(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb on EL 10.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_mariadb_odbc_driver_dnf(
        csp_container,
        odbc_driver,
        # package is for EL9
        'https://downloads.mariadb.com/Connectors/odbc/connector-odbc-3.2.6/mariadb-connector-odbc-3.2.6-1.el9.x86_64.rpm')

def configure_odbc_driver_almalinux_10_mariadb_114(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 11.4 almalinux 10.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el_10_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_almalinux_10_mariadb_118(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 11.8 almalinux 10.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el_10_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_10_mariadb_114(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 11.4 rockylinux 10.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el_10_mariadb(csp_container, odbc_driver)

def configure_odbc_driver_rockylinux_10_mariadb_118(csp_container, odbc_driver):
    """Configure ODBC driver for mariadb 11.8 rockylinux 10.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_odbc_driver_el_10_mariadb(csp_container, odbc_driver)

def configure_odbc_driver(platform_image, database_image, csp_container, odbc_driver=None):
    """Make an ODBC setup strategy for the given database type.

    Arguments:
    platform_image -- repo:tag for the docker image of the platform running the iRODS servers
    database_image -- repo:tag for the docker image of the database server
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- if specified, the ODBC driver will be sought here
    """
    import inspect

    base_name = inspect.currentframe().f_code.co_name
    pf_part = context.sanitize(f"{context.image_repo(platform_image)}_{context.image_tag(platform_image)}")
    db_part = context.sanitize(f"{context.image_repo(database_image)}_{context.image_tag(database_image)}")

    func = globals().get(f'{base_name}_{pf_part}_{db_part}')
    if func:
        return func(csp_container, odbc_driver)

    raise NameError(
        f"no ODBC configuration function found for platform [{platform_image}] and database [{database_image}]"
    )
