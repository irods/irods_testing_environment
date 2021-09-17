# grown-up modules
import compose.cli.command
import docker
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


def install_packages_on_container_from_tarfile(docker_client,
                                               platform_name,
                                               container_name,
                                               package_paths,
                                               tarfile_path):
    """Install specified packages from specified tarfile on specified container.

    Arguments:
    docker_client -- docker client for interacting with the docker-compose project
    platform_name -- name of the OS platform on which packages are being installed
    container_name -- name of the container on which packages are being installed
    package_paths -- full paths to where the packages will be inside the container
    tarfile_path -- full path to the tarfile on the host to be copied into hte container
    """
    container = docker_client.containers.get(container_name)

    # Only the iRODS containers need to have packages installed
    if context.is_catalog_database_container(container): return 0

    archive.copy_archive_to_container(container, tarfile_path)

    package_list = ' '.join([
        p for p in package_paths
        if not context.is_database_plugin(p) or
           context.is_irods_catalog_provider_container(container)])

    cmd = ' '.join([platform_install_local_packages_command(platform_name), package_list])

    logging.warning('executing cmd [{0}] on container [{1}]'.format(cmd, container.name))

    ec = execute.execute_command(container, platform_update_command(platform_name))
    if ec is not 0:
        logging.error('failed to update local repositories [{}]'.format(container.name))
        return ec

    ec = execute.execute_command(container, cmd)
    if ec is not 0:
        logging.error(
            'failed to install packages on container [ec=[{0}], container=[{1}]'.format(ec, container.name))
        return ec

    return 0


def install_packages(docker_client, platform_name, package_directory, containers, package_name_list=None):
    import concurrent.futures

    packages = get_list_of_package_paths(platform_name, package_directory, package_name_list)

    logging.info('packages to install [{}]'.format(packages))

    tarfile_path = archive.create_archive(packages)

    rc = 0
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures_to_containers = {
            executor.submit(
                install_packages_on_container_from_tarfile,
                docker_client, platform_name, c.name, packages, tarfile_path
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


def install_official_irods_packages(docker_client, platform_name, database_name, version, containers):
    def install_packages_(docker_client, docker_compose_container, packages_list, platform_name):
        # Only the iRODS containers need to have packages installed
        if context.is_catalog_database_container(docker_compose_container):
            return 0

        container = docker_client.containers.get(docker_compose_container.name)

        package_list = ' '.join([p for p in packages_list if not context.is_database_plugin(p) or context.is_irods_catalog_provider_container(container)])

        cmd = ' '.join([platform_install_official_packages_command(platform_name), package_list])

        logging.warning('executing cmd [{0}] on container [{1}]'.format(cmd, container.name))

        ec = execute.execute_command(container, platform_update_command(platform_name))
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

    package_name_list = ['irods-runtime', 'irods-icommands', 'irods-server', 'irods-database-plugin-{}'.format(database_name)]

    # If a version is not provided, just install the latest
    if version:
        packages = ['{}={}'.format(p, version) for p in package_name_list]
    else:
        packages = package_name_list

    logging.info('packages to install [{}]'.format(packages))

    rc = 0
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures_to_containers = {executor.submit(install_packages_, docker_client, c, packages, platform_name): c for c in containers}
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


if __name__ == "__main__":
    import argparse
    import logs
    import textwrap

    import cli

    parser = argparse.ArgumentParser(description='Install iRODS packages to a docker-compose project.')

    cli.add_common_args(parser)
    cli.add_compose_args(parser)
    cli.add_irods_package_args(parser)

    parser.add_argument('--irods-catalog-provider-service-instance',
                        metavar='IRODS_CATALOG_PROVIDER_INSTANCE_NUM',
                        dest='irods_csp_instance', type=int, default=1,
                        help=textwrap.dedent('''\
                            The Compose service instance number of the iRODS catalog service \
                            provider.'''))

    parser.add_argument('--irods-catalog-consumer-service-instances',
                        metavar='IRODS_CATALOG_CONSUMER_INSTANCE_NUM',
                        dest='irods_csc_instances', type=int, nargs='+',
                        help=textwrap.dedent('''\
                            The Compose service instance numbers of the iRODS catalog service \
                            consumers.'''))

    args = parser.parse_args()

    if args.package_directory and args.package_version:
        print('package directory and package version are mutually exclusive')
        exit(1)

    logs.configure(args.verbosity)

    docker_client = docker.from_env()

    project_directory = args.project_directory or os.getcwd()

    compose_project = compose.cli.command.get_project(
        project_dir=os.path.abspath(project_directory),
        project_name=args.project_name)

    logging.debug('provided project name [{0}], docker-compose project name [{1}]'
                  .format(args.project_name, compose_project.name))

    project_name = args.project_name or compose_project.name

    if len(compose_project.containers()) is 0:
        logging.critical(
            'no containers found for project [directory=[{0}], name=[{1}]]'.format(
            os.path.abspath(project_directory), project_name))

        exit(1)

    logging.debug('containers on project [{}]'.format(
                  [c.name for c in compose_project.containers()]))

    platform, database = cli.platform_and_database(docker_client, compose_project)

    # TODO: allow specifying containers by service instance
    target_containers = compose_project.containers()

    if args.irods_externals_package_directory:
        ec = install_packages(docker_client,
                              context.image_repo(platform),
                              os.path.abspath(args.irods_externals_package_directory),
                              target_containers,
                              context.irods_externals_package_names())
        if ec is not 0:
            exit(ec)

    # TODO: allow specifying package names
    if args.package_directory:
        exit(install_packages(docker_client,
                              context.image_repo(platform),
                              os.path.abspath(args.package_directory),
                              target_containers,
                              context.irods_package_names(context.image_repo(database))))

    # Even if no version was provided, we default to using the latest official release
    exit(install_official_irods_packages(docker_client,
                                         context.image_repo(platform),
                                         context.image_repo(database),
                                         args.package_version,
                                         target_containers))
