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


def get_list_of_package_paths(platform_name, package_directory, package_name_list):
    import glob

    if not package_directory:
        raise RuntimeError('Attempting to install custom packages from unspecified location')

    package_path = os.path.abspath(package_directory)

    logging.debug('listing for [{}]:\n{}'.format(package_path, os.listdir(package_path)))

    packages = list()

    for p in package_name_list:
        p_glob = os.path.join(package_path, p + '*.{}'.format(package_filename_extension(platform_name)))

        logging.debug('looking for packages like [{}]'.format(p_glob))

        glob_list = glob.glob(p_glob)

        if len(glob_list) is 0:
            raise RuntimeError('no packages found [{}]'.format(p_glob))

        packages.append(glob_list[0])

    return packages

def is_package_database_plugin(p):
    return 'database' in p


# TODO: Want to make a more generic version of this
def install_local_irods_packages(docker_client, platform_name, database_name, package_directory, containers):
    def install_packages(docker_client, docker_compose_container, packages_list, packages_tarfile_path, platform_name):
        # Only the iRODS containers need to have packages installed
        if context.is_catalog_database_container(docker_compose_container):
            return 0

        container = docker_client.containers.get(docker_compose_container.name)

        path_to_packages_in_container = archive.copy_archive_to_container(container, packages_tarfile_path)

        package_list = ' '.join([p for p in packages_list if not is_package_database_plugin(p) or context.is_irods_catalog_provider_container(container)])

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

    import concurrent.futures

    package_name_list = ['irods-runtime', 'irods-icommands', 'irods-server', 'irods-database-plugin-{}'.format(database_name)]

    packages = get_list_of_package_paths(platform_name, package_directory, package_name_list)

    logging.info('packages to install [{}]'.format(packages))

    # TODO: output directory should contain the tarfile of packages for archaeological purposes
    tarfile_path = archive.create_archive(packages)

    rc = 0
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures_to_containers = {executor.submit(install_packages, docker_client, c, packages, tarfile_path, platform_name): c for c in containers}
        logging.debug(futures_to_containers)

        for f in concurrent.futures.as_completed(futures_to_containers):
            container = futures_to_containers[f]
            try:
                ec = f.result()
                if ec is not 0:
                    logging.error('error while installing packages on container [{}]'.format(container.name))
                    rc = ec
                else:
                    logging.info('packages installed successfully [{}]'.format(container.name))

            except Exception as e:
                logging.error('exception raised while installing packages [{}]'.format(container.name))
                logging.error(e)
                rc = 1

    return rc


def install_official_irods_packages(docker_client, platform_name, database_name, version, containers):
    def install_packages(docker_client, docker_compose_container, packages_list, platform_name):
        # Only the iRODS containers need to have packages installed
        if context.is_catalog_database_container(docker_compose_container):
            return 0

        container = docker_client.containers.get(docker_compose_container.name)

        package_list = ' '.join([p for p in packages_list if not is_package_database_plugin(p) or context.is_irods_catalog_provider_container(container)])

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
        packages = ['{0}={1}'.format(p, version) for p in package_name_list]
    else:
        packages = package_name_list

    logging.info('packages to install [{}]'.format(packages))

    rc = 0
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures_to_containers = {executor.submit(install_packages, docker_client, c, packages, platform_name): c for c in containers}
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

    parser = argparse.ArgumentParser(description='Install iRODS packages to a docker-compose project.')
    parser.add_argument('--package-directory', metavar='PATH_TO_DIRECTORY_WITH_PACKAGES', type=str, dest='package_directory',
                        help='Path to local directory which contains iRODS packages to be installed.')
    parser.add_argument('--package-version', metavar='PACKAGE_VERSION_TO_DOWNLOAD', type=str, dest='package_version',
                        help='Version of iRODS to download and install.')
    parser.add_argument('--project-directory', metavar='PATH_TO_PROJECT_DIRECTORY', type=str, dest='project_directory',
                        help='Path to the docker-compose project on which packages will be installed. (Default: $(pwd))')
    parser.add_argument('--project-name', metavar='PROJECT_NAME', type=str, dest='project_name',
                        help='Name of the docker-compose project on which to install packages.')
    parser.add_argument('--os-platform-tag', '-p', metavar='OS_PLATFORM_IMAGE_TAG', dest='platform', type=str,
                        help='The tag of the base Docker image to use.')
    parser.add_argument('--database-tag', '-d', metavar='DATABASE_IMAGE_TAG', dest='database', type=str,
                        help='The tag of the database container to use.')
    parser.add_argument('--verbose', '-v', dest='verbosity', action='count', default=1,
                        help='Increase the level of output to stdout. CRITICAL and ERROR messages will always be printed.')

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

    logging.debug('containers on project [{}]'.format([c.name for c in compose_project.containers()]))

    platform = args.platform
    if not platform:
        platform = context.image_repo_and_tag_string(
            context.platform_image_repo_and_tag(project_name)
        )

        logging.debug('derived os platform image tag [{}]'.format(platform))

    database = args.database
    if not database:
        database = context.image_repo_and_tag_string(
            context.database_image_repo_and_tag(project_name))

        logging.debug('derived database image tag [{}]'.format(database))

    if args.package_directory:
        exit(
            install_local_irods_packages(
                docker.from_env(),
                context.image_repo(platform),
                context.image_repo(database),
                os.path.abspath(args.package_directory),
                compose_project.containers()
            )
        )

    # Even if no version was provided, we default to using the latest official release
    exit(
        install_official_irods_packages(
            docker.from_env(),
            context.image_repo(platform),
            context.image_repo(database),
            args.package_version,
            compose_project.containers()
        )
    )
