# grown-up modules
import docker
import logging
import os

# local modules
import archive
import context

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

def collect_logs(docker_client, containers, output_directory, logfile_path=None):
    if not logfile_path:
        logfile_path = os.path.join(context.irods_home(), 'log')

    for c in containers:
        od = os.path.join(output_directory, 'logs', c.name)
        if not os.path.exists(od):
            os.makedirs(od)

        logging.info('saving log to [{}] [{}]'.format(od, c.name))

        archive.copy_from_container(docker_client.containers.get(c.name),
                                    logfile_path,
                                    path_to_destination_directory_on_host=od)
