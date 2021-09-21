# grown-up modules
import logging

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
