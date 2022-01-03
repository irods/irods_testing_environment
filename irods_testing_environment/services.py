# grown-up modules
import logging
import os

# local modules
import context
import install
import irods_setup

def create_topology(ctx,
                    externals_directory=None,
                    package_directory=None,
                    package_version=None,
                    odbc_driver=None,
                    consumer_count=0):
    """Create a generic topology of iRODS servers with the given inputs.

    This is a convenience function for standing up an iRODS Zone with the default
    setup parameters.

    Arguments:
    ctx -- context object which holds the Docker client and Compose project information
    externals_directory -- path to directory in which iRODS externals packages are housed
    package_directory -- path to directory in which iRODS packages are housed
    package_version -- version tag for official iRODS packages to download and install
    odbc_driver -- path to archive file containing an ODBC driver to use with iRODS CSP
    consumer_count -- number of iRODS CSCs to create and set up for the Zone
    """
    ctx.compose_project.up(scale_override={
        context.irods_catalog_consumer_service(): consumer_count
    })

    install.install_irods_packages(ctx,
                                   externals_directory=externals_directory,
                                   package_directory=package_directory,
                                   package_version=package_version)

    irods_setup.setup_irods_zone(ctx, odbc_driver=odbc_driver)


def clone_repository_to_container(container,
                                  repo_name,
                                  url_base='https://github.com/irods',
                                  branch=None,
                                  destination_directory=None):
    """Clone the specified git repository to the specified container.

    Arguments:
    container -- target container on which the test script will run
    repo_name -- name of the git repo
    url_base -- base of the git URL from which the repository will be cloned
    branch -- branch name to checkout in the cloned repository
    destination_directory -- path on local filesystem to which git repository will be cloned
    """
    import tempfile
    from git import Repo

    import archive

    url = os.path.join(url_base, '.'.join([repo_name, 'git']))

    repo_path = os.path.abspath(os.path.join(
                    destination_directory or tempfile.mkdtemp(),
                    repo_name))

    Repo().clone_from(url=url, to_path=repo_path, branch=branch)

    archive.copy_archive_to_container(container,
                                      archive.create_archive(
                                            [os.path.abspath(repo_path)], repo_name))

    return repo_path

