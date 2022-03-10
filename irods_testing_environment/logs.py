# grown-up modules
import docker
import logging
import os

# local modules
from . import archive
from . import context

# TODO: Maybe this should be some kind of builder
def configure(verbosity=1, log_filename=None):
    # CRITICAL messages will always be printed, but anything after that is a function of the number of -v
    level = logging.CRITICAL - 10 * verbosity

    handlers = [logging.StreamHandler()]

    if log_filename:
        handlers.append(logging.FileHandler(os.path.abspath(log_filename)))

    logging.basicConfig(
        level = level if level > logging.NOTSET else logging.DEBUG,
        format = '%(asctime)-15s %(levelname)s - %(message)s',
        handlers = handlers
    )


def log_directory_for_version(version):
    """Return default iRODS log directory for the given `version`."""
    major,minor,patch = version

    if int(major) < 4:
        raise NotImplementedError('nothing prior to iRODS 4.0.0 is supported right now')

    if int(major) > 4:
        raise NotImplementedError('the detected iRODS version does not exist yet')

    if int(minor) < 2:
        return os.path.join(context.irods_home(), 'iRODS', 'log')
    elif int(minor) < 3:
        return os.path.join(context.irods_home(), 'log')
    elif int(minor) < 4:
        return os.path.join('/var', 'log', 'irods')

    raise NotImplementedError('the detected iRODS version does not exist yet')


def collect_logs(docker_client, containers, output_directory):
    """Collect logs from known locations for iRODS log files.

    Arguments:
    docker_client -- the Docker client which communicates with the daemon
    containers -- list of containers from which logs will be collected
    output_directory -- directory on host into which log files will be collected
    """
    return archive.collect_files_from_containers(docker_client,
                                                 containers,
                                                 [log_directory_for_version((4,3,0)),
                                                  log_directory_for_version((4,2,0))],
                                                 output_directory)
