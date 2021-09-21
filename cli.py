# grown-up modules
import logging

# local modules
import context
import textwrap

def add_compose_args(parser):
    '''Add argparse options related to Docker Compose project.

    Arguments:
    parser -- argparse.ArgumentParser to augment
    '''
    parser.add_argument('--project-directory',
                        metavar='PATH_TO_PROJECT_DIRECTORY',
                        dest='project_directory',
                        default='.',
                        help='Path to Compose project on which packages will be installed.')

    parser.add_argument('--project-name',
                        metavar='PROJECT_NAME',
                        dest='project_name',
                        help='Name of Compose project on which to install packages.')

def add_irods_package_args(parser):
    '''Add argparse options related to to-be-installed iRODS packages.

    Arguments:
    parser -- argparse.ArgumentParser to augment
    '''
    parser.add_argument('--irods-package-directory',
                        metavar='PATH_TO_DIRECTORY_WITH_PACKAGES',
                        dest='package_directory',
                        help='Path to local directory which contains iRODS packages.')

    parser.add_argument('--irods-package-version',
                        metavar='PACKAGE_VERSION_TO_DOWNLOAD',
                        dest='package_version',
                        help=textwrap.dedent('''\
                            Version of official iRODS packages to download and install. \
                            If neither this or --package-directory are specified, \
                            the latest available version will be installed.'''))

    parser.add_argument('--irods-externals-package-directory',
                        metavar='PATH_TO_DIRECTORY_WITH_IRODS_EXTERNALS_PACKAGES',
                        dest='irods_externals_package_directory',
                        help='Path to local directory which contains iRODS externals packages.')


def add_database_config_args(parser):
    '''Add argparse options related to setting up and configuring iRODS.

    Arguments:
    parser -- argparse.ArgumentParser to augment
    '''
    parser.add_argument('--odbc-driver-path',
                        metavar='PATH_TO_ODBC_DRIVER_ARCHIVE',
                        dest='odbc_driver',
                        help=textwrap.dedent('''\
                            Path to the ODBC driver archive file on the local machine. \
                            If not provided, the driver will be downloaded.'''))

def add_common_args(parser):
    '''Add argparse options common to irods_testing_environment scripts.

    Arguments:
    parser -- argparse.ArgumentParser to augment
    '''
    parser.add_argument('--verbose', '-v',
                        dest='verbosity', action='count', default=1,
                        help=textwrap.dedent('''\
                            Increase the level of output to stdout. \
                            CRITICAL and ERROR messages will always be printed. \
                            Add more to see more log messages (e.g. -vvv displays DEBUG).'''))
