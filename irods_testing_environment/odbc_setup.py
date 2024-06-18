# grown-up modules
import logging
import os
import textwrap

# local modules
from . import archive
from . import context
from . import execute

def configure_postgres_odbc_driver(csp_container, odbc_driver):
    """Configure ODBC driver for postgres.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    logging.debug('no ODBC driver setup required for postgres [{}]'.format(csp_container))


def configure_odbc_driver_ubuntu_2004_postgres_1012(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 10.12 on ubuntu 20.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_ubuntu_2004_postgres_148(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 14.8 on ubuntu 20.04.

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

def configure_odbc_driver_ubuntu_2204_postgres_148(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 14.8 on ubuntu 22.04.

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

def configure_odbc_driver_ubuntu_2404_postgres_148(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 14.8 on ubuntu 24.04.

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

def configure_odbc_driver_debian_11_postgres_1012(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 10.12 on debian 11.

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

def configure_odbc_driver_debian_12_postgres_148(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 14.8 on debian 12.

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

def configure_odbc_driver_centos_7_postgres_1012(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 10.12 on centos 7.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_centos_7_postgres_16(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 16 on centos 7.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    configure_postgres_odbc_driver(csp_container, odbc_driver)

def configure_odbc_driver_almalinux_8_postgres_1012(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 10.12 on almalinux 8.

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

def configure_odbc_driver_rockylinux_8_postgres_1012(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 10.12 on rockylinux 8.

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

def configure_odbc_driver_rockylinux_9_postgres_148(csp_container, odbc_driver):
    """Configure ODBC driver for postgres 14.8 on rockylinux 9.

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

def make_mysql_odbcinst_ini(csp_container, container_odbc_driver_dir):
    """Generate content for the /etc/odbcinst.ini configuration file used by mysql.

    Arguments:
    csp_container -- container running iRODS catalog service provider using the ODBC driver
    container_odbc_driver_dir -- path in `csp_container` containing the ODBC driver directory
    """
    odbcinst_ini_path = os.path.join('/etc', 'odbcinst.ini')

    if 'mysql-connector-odbc-8.0.' in container_odbc_driver_dir:
        logging.debug('configuring odbcinst.ini with MySQL 8.0 drivers')
        odbcinst_ini_contents = textwrap.dedent("""\
            [MySQL ANSI]
            Description = MySQL ODBC 8.0 ANSI Driver
            Driver = {0}/lib/libmyodbc8a.so

            [MySQL Unicode]
            Description = MySQL ODBC 8.0 Unicode Driver
            Driver = {0}/lib/libmyodbc8w.so""".format(container_odbc_driver_dir))
    else:
        logging.debug('configuring odbcinst.ini with MySQL 5.3 drivers')
        odbcinst_ini_contents = textwrap.dedent("""\
            [MySQL ANSI]
            Description = MySQL ODBC 5.3 ANSI Driver
            Driver = {0}/lib/libmyodbc5a.so

            [MySQL Unicode]
            Description = MySQL ODBC 5.3 Unicode Driver
            Driver = {0}/lib/libmyodbc5w.so""".format(container_odbc_driver_dir))

    cmd = 'bash -c \'echo "{0}" > {1}\''.format(odbcinst_ini_contents, odbcinst_ini_path)
    ec = execute.execute_command(csp_container, cmd)
    if ec is not 0:
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


def configure_odbc_driver_centos_7_mysql_8029(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on centos 7.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    if not odbc_driver:
        odbc_driver = download_mysql_odbc_driver(
            'https://downloads.mysql.com/archives/get/p/10/file/mysql-connector-odbc-8.0.29-linux-glibc2.12-x86-64bit.tar.gz')

    configure_mysql_odbc_driver(csp_container, os.path.abspath(odbc_driver))


def configure_odbc_driver_ubuntu_2004_mysql_8029(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on ubuntu 20.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    if not odbc_driver:
        odbc_driver = download_mysql_odbc_driver(
            'https://dev.mysql.com/get/Downloads/Connector-ODBC/8.0/mysql-connector-odbc-8.0.29-linux-glibc2.12-x86-64bit.tar.gz')

    configure_mysql_odbc_driver(csp_container, os.path.abspath(odbc_driver))


def configure_odbc_driver_ubuntu_2204_mysql_8029(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on ubuntu 22.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    if not odbc_driver:
        odbc_driver = download_mysql_odbc_driver(
            'https://dev.mysql.com/get/Downloads/Connector-ODBC/8.0/mysql-connector-odbc-8.0.29-linux-glibc2.12-x86-64bit.tar.gz')

    configure_mysql_odbc_driver(csp_container, os.path.abspath(odbc_driver))


def configure_odbc_driver_ubuntu_2404_mysql_8033(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on ubuntu 24.04.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    if not odbc_driver:
        odbc_driver = download_mysql_odbc_driver(
            'https://dev.mysql.com/get/Downloads/Connector-ODBC/8.0/mysql-connector-odbc-8.0.33-linux-glibc2.28-x86-64bit.tar.gz')

    configure_mysql_odbc_driver(csp_container, os.path.abspath(odbc_driver))


def configure_odbc_driver_debian_11_mysql_8029(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on debian 11.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    if not odbc_driver:
        odbc_driver = download_mysql_odbc_driver(
            'https://dev.mysql.com/get/Downloads/Connector-ODBC/8.0/mysql-connector-odbc-8.0.29-linux-glibc2.12-x86-64bit.tar.gz')

    configure_mysql_odbc_driver(csp_container, os.path.abspath(odbc_driver))

def configure_odbc_driver_debian_12_mysql_8029(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on debian 12.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    if not odbc_driver:
        odbc_driver = download_mysql_odbc_driver(
            'https://dev.mysql.com/get/Downloads/Connector-ODBC/8.0/mysql-connector-odbc-8.0.29-linux-glibc2.12-x86-64bit.tar.gz')

    configure_mysql_odbc_driver(csp_container, os.path.abspath(odbc_driver))


def configure_odbc_driver_almalinux_8_mysql_8029(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on almalinux 8.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    if not odbc_driver:
        odbc_driver = download_mysql_odbc_driver(
            'https://dev.mysql.com/get/Downloads/Connector-ODBC/8.0/mysql-connector-odbc-8.0.29-linux-glibc2.12-x86-64bit.tar.gz')

    configure_mysql_odbc_driver(csp_container, os.path.abspath(odbc_driver))


def configure_odbc_driver_rockylinux_8_mysql_8029(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on rockylinux 8.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    if not odbc_driver:
        odbc_driver = download_mysql_odbc_driver(
            'https://dev.mysql.com/get/Downloads/Connector-ODBC/8.0/mysql-connector-odbc-8.0.29-linux-glibc2.12-x86-64bit.tar.gz')

    configure_mysql_odbc_driver(csp_container, os.path.abspath(odbc_driver))

def configure_odbc_driver_rockylinux_9_mysql_8029(csp_container, odbc_driver):
    """Configure ODBC driver for mysql 8.0 on rockylinux 9.

    Argument:
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- path to local archive file containing the ODBC driver package
    """
    if not odbc_driver:
        odbc_driver = download_mysql_odbc_driver(
            'https://dev.mysql.com/get/Downloads/Connector-ODBC/8.0/mysql-connector-odbc-8.0.29-linux-glibc2.12-x86-64bit.tar.gz')

    configure_mysql_odbc_driver(csp_container, os.path.abspath(odbc_driver))

def configure_odbc_driver(platform_image, database_image, csp_container, odbc_driver=None):
    """Make an ODBC setup strategy for the given database type.

    Arguments:
    platform_image -- repo:tag for the docker image of the platform running the iRODS servers
    database_image -- repo:tag for the docker image of the database server
    csp_container -- docker container on which the iRODS catalog service provider is running
    odbc_driver -- if specified, the ODBC driver will be sought here
    """
    import inspect
    # generate the function name of the form:
    #   configure_odbc_driver_platform-repo_platform-tag_database-repo_database-tag
    func_name = '_'.join([inspect.currentframe().f_code.co_name,
                          context.sanitize(context.image_repo(platform_image)),
                          context.sanitize(context.image_tag(platform_image)),
                          context.sanitize(context.image_repo(database_image)),
                          context.sanitize(context.image_tag(database_image))])

    eval(func_name)(csp_container, odbc_driver)

