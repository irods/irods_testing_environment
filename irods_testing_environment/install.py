# grown-up modules
import logging
import os

# local modules
import archive
import context
import execute

def platform_update_command(platform):
    if 'centos' in platform:
        return 'yum update -y'
    elif 'ubuntu' in platform:
        return 'apt update'
    else:
        raise RuntimeError('unsupported platform [{}]'.format(platform))


def platform_install_local_packages_command(platform):
    if 'centos' in platform:
        return 'yum --nogpgcheck -y install'
        #return 'rpm -U --force'
    elif 'ubuntu' in platform:
        return 'apt install -fy'
    else:
        raise RuntimeError('unsupported platform [{}]'.format(platform))


def platform_install_official_packages_command(platform):
    if 'centos' in platform:
        return 'yum -y install'
    elif 'ubuntu' in platform:
        return 'apt install -y'
    else:
        raise RuntimeError('unsupported platform [{}]'.format(platform))


def package_filename_extension(platform):
    if 'centos' in platform:
        return 'rpm'
    elif 'ubuntu' in platform:
        return 'deb'
    else:
        raise RuntimeError('unsupported platform [{}]'.format(platform))


def package_version_joinery(platform):
    if 'centos' in platform:
        return '-'
    elif 'ubuntu' in platform:
        return '='
    else:
        raise RuntimeError('unsupported platform [{}]'.format(platform))


def install_pip_package_from_repo(container,
                                  repo_name,
                                  url_base='https://github.com/irods',
                                  branch=None):
    """Installs a pip package from a git repository cloned from the specified location.

    Arguments:
    container -- container on which pip packages are to be installed
    repo_name -- name of the git repository to clone
    branch -- branch to checkout in cloned git repository
    """
    import services

    repo_path = services.clone_repository_to_container(container,
                                                       repo_name,
                                                       url_base=url_base,
                                                       branch=branch)
    ec = execute.execute_command(container, 'pip install -e {}'.format(repo_path))
    if ec is not 0:
        raise RuntimeError('Failed to install pip package [{}] [{}]'
                           .format(repo_path, container.name))


def get_list_of_package_paths(platform_name, package_directory, package_name_list=None):
    import glob

    if not package_directory:
        raise RuntimeError('Attempting to install custom packages from unspecified location')

    # If nothing is provided, installs everything in package_directory
    if not package_name_list:
        package_name_list = ['']

    package_path = os.path.abspath(package_directory)

    logging.debug('listing for [{}]:\n{}'.format(package_path, os.listdir(package_path)))

    packages = list()

    for p in package_name_list:
        glob_str = os.path.join(package_path, p + '*.{}'.format(package_filename_extension(platform_name)))

        logging.debug('looking for packages like [{}]'.format(glob_str))

        glob_list = glob.glob(glob_str)

        if len(glob_list) is 0:
            raise RuntimeError('no packages found [{}]'.format(glob_str))

        # TODO: allow specifying a suffix or something instead of taking everything
        for item in glob_list:
            packages.append(item)

    return packages


def install_packages_on_container_from_tarfile(ctx,
                                               container_name,
                                               package_paths,
                                               tarfile_path):
    """Install specified packages from specified tarfile on specified container.

    Arguments:
    ctx -- context object which contains a docker_client
    container_name -- name of the container on which packages are being installed
    package_paths -- full paths to where the packages will be inside the container
    tarfile_path -- full path to the tarfile on the host to be copied into hte container
    """
    container = ctx.docker_client.containers.get(container_name)

    # Only the iRODS containers need to have packages installed
    if context.is_catalog_database_container(container): return 0

    archive.copy_archive_to_container(container, tarfile_path)

    package_list = ' '.join([
        p for p in package_paths
        if not context.is_database_plugin(p) or
           context.is_irods_catalog_provider_container(container)])

    cmd = ' '.join([platform_install_local_packages_command(ctx.platform_name()), package_list])

    logging.warning('executing cmd [{0}] on container [{1}]'.format(cmd, container.name))

    ec = execute.execute_command(container, platform_update_command(ctx.platform_name()))
    if ec is not 0:
        logging.error('failed to update local repositories [{}]'.format(container.name))
        return ec

    ec = execute.execute_command(container, cmd)
    if ec is not 0:
        logging.error(
            'failed to install packages on container [ec=[{0}], container=[{1}]'.format(ec, container.name))
        return ec

    return 0


def install_packages(ctx, package_directory, containers, package_name_list=None):
    import concurrent.futures

    packages = get_list_of_package_paths(ctx.platform_name(), package_directory, package_name_list)

    logging.info('packages to install [{}]'.format(packages))

    tarfile_path = archive.create_archive(packages)

    rc = 0
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures_to_containers = {
            executor.submit(
                install_packages_on_container_from_tarfile,
                ctx, c.name, packages, tarfile_path
            ): c for c in containers
        }
        logging.debug(futures_to_containers)

        for f in concurrent.futures.as_completed(futures_to_containers):
            container = futures_to_containers[f]
            try:
                ec = f.result()
                if ec is not 0:
                    logging.error('error while installing packages on container [{}]'
                                  .format(container.name))
                    rc = ec
                else:
                    logging.info('packages installed successfully [{}]'
                                 .format(container.name))

            except Exception as e:
                logging.error('exception raised while installing packages [{}]'
                              .format(container.name))
                logging.error(e)
                rc = 1

    return rc


def install_official_irods_packages(ctx, version, containers):
    def install_packages_(ctx, docker_compose_container, packages_list):
        container = ctx.docker_client.containers.get(docker_compose_container.name)

        package_list = ' '.join([p for p in packages_list if not context.is_database_plugin(p) or context.is_irods_catalog_provider_container(container)])

        cmd = ' '.join([platform_install_official_packages_command(ctx.platform_name()), package_list])

        logging.warning('executing cmd [{0}] on container [{1}]'.format(cmd, container.name))

        ec = execute.execute_command(container, platform_update_command(ctx.platform_name()))
        if ec is not 0:
            logging.error('failed to update local repositories [{}]'.format(container.name))
            return ec

        ec = execute.execute_command(container, cmd)
        if ec is not 0:
            logging.error(
                'failed to install packages on container [ec=[{0}], container=[{1}]'.format(ec, container.name))

            return ec

        return 0

    import concurrent.futures

    # If a version is not provided, just install the latest
    if version:
        packages = ['{}{}{}'.format(p, package_version_joinery(ctx.platform_name()), version)
                    for p in context.irods_package_names(ctx.database_name())]
    else:
        packages = context.irods_package_names(ctx.database_name())

    logging.info('packages to install [{}]'.format(packages))

    rc = 0
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures_to_containers = {executor.submit(install_packages_, ctx, c, packages): c for c in containers}
        logging.debug(futures_to_containers)

        for f in concurrent.futures.as_completed(futures_to_containers):
            container = futures_to_containers[f]
            try:
                ec = f.result()
                if ec is not 0:
                    logging.error('error while installing packages on container [{}]'.format(container.name))
                    rc = ec

                logging.info('packages installed successfully [{}]'.format(container.name))

            except Exception as e:
                logging.error('exception raised while installing packages [{}]'.format(container.name))
                logging.error(e)
                rc = 1

    return rc


def install_irods_packages(ctx,
                           externals_directory=None,
                           package_directory=None,
                           package_version=None):
    """Install iRODS packages and external dependencies.

    `package_directory` and `package_version` cannot both be specified.

    Arguments:
    ctx -- a context object which holds information about the Compose environment
    externals_directory -- path to directory on local machine in which iRODS externals
                           packages are located (if None, externals are installed using the
                           dependencies declared in the iRODS packages which are downloaded
                           from the Internet and installed)
    package_directory -- path to directory on local machine in which iRODS packages are
                         located (if None, official packages from the Internet are downloaded
                         and installed instead)
    package_version -- version string for iRODS packages to download from the Internet and
                       install (if None, the latest available version is used)
    """
    if package_directory and package_version:
        raise ValueError('package_directory and package_version are incompatible')

    if externals_directory:
        ec = install_packages(ctx,
                              os.path.abspath(irods_externals_package_directory),
                              ctx.irods_containers(),
                              context.irods_externals_package_names())
        if ec is not 0:
            raise RuntimeError('failed to install externals')

    if package_directory:
        logging.warning('installing iRODS packages from directory [{}]'
                        .format(package_directory))

        ec = install_packages(ctx,
                              os.path.abspath(package_directory),
                              ctx.irods_containers(),
                              context.irods_package_names(ctx.database_name()))
        if ec is not 0:
            raise RuntimeError('failed to install iRODS packages')

    else:
        # Even if no version was provided, we default to using the latest official release
        logging.warning('installing official iRODS packages [{}]'
                        .format(package_version))

        ec = install_official_irods_packages(ctx, package_version, ctx.irods_containers())
        if ec is not 0:
            raise RuntimeError('failed to install iRODS packages')
