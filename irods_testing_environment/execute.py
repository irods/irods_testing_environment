# grown-up modules
import compose.cli.command
import docker
import logging
import os

# local modules
from . import context

def execute_command(container, command, user='', workdir=None, stream_output=False):
    OUTPUT_ENCODING = 'utf-8'

    logging.debug('executing on [{0}] [{1}]'.format(container.name, command))

    exec_instance = container.client.api.exec_create(container.id, command, user=user, workdir=workdir)
    exec_out = container.client.api.exec_start(exec_instance['Id'], stream=stream_output)

    previous_log_level = logging.getLogger().getEffectiveLevel()
    if previous_log_level > logging.INFO:
        logging.getLogger().setLevel(logging.INFO)

    try:
        # Stream output from the executing command. A StopIteration exception is raised
        # by the generator returned by the docker-py API when there is no more output.
        while stream_output:
            out = next(exec_out).decode(OUTPUT_ENCODING)
            logging.info(out)

    except StopIteration:
        logging.debug('done')

    finally:
        logging.getLogger().setLevel(previous_log_level)

    if not stream_output:
        logging.debug(exec_out.decode(OUTPUT_ENCODING))

    return container.client.api.exec_inspect(exec_instance['Id'])['ExitCode']
