# grown-up modules
import logging

# local modules
import context
import textwrap

def add_platform_args(parser):
    '''Add argparse options related to database/platform specification.

    Arguments:
    parser -- argparse.ArgumentParser to augment
    '''
    parser.add_argument('--os-platform-image', '-p',
                        metavar='OS_PLATFORM_IMAGE_REPO_AND_TAG',
                        dest='platform',
                        help='The repo:tag of the OS platform image to use')

    parser.add_argument('--database-image', '-d',
                        metavar='DATABASE_IMAGE_REPO_AND_TAG',
                        dest='database',
                        help='The repo:tag of the database image to use')

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

def platform_and_database(platform, database, project_name=None):
    '''Return tuple of platform and database Docker image tags based on provided arguments.

    If platform and database are not None, these will serve as the platform and database pieces
    of the returned tuple, respectively. If neither are known, the project_name is consulted,
    with the expectation that it is a string of the following form:
        (.*-<platform_name>-<platform_version>-<database_name>-<database_version>)

    If platform, database, and project are None, an error will occur.

    Arguments:
    platform -- The platform Docker image tag. If unknown, None should be passed.
    database -- The database Docker image tag. If unknown, None should be passed.
    project_name -- The Compose project name from which the platform/database are divined.
    '''
    return (
        platform or context.image_repo_and_tag_string(
            context.platform_image_repo_and_tag(project_name)),

        database or context.image_repo_and_tag_string(
            context.database_image_repo_and_tag(project_name))
    )
