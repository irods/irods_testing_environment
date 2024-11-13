# grown-up modules
import logging

def execute_command(container, command, user='', workdir=None, stream_output=None):
    """Execute `command` in `container` as `user` in `workdir`.

    Running this is equivalent to the following:
        docker exec -u <user> -w <workdir> <container> <command>

    Arguments:
    container -- container in which the command will be run
    command -- string representing the command to run
    user -- the user whose identity will be assumed when running the command (default: root)
    workdir -- the present working directory for the command (default: root directory)
    stream_output -- a boolean value to indicate that output from the command execution should
                     be streamed to the logging module. If None is used, a decision is made for
                     the user: If the log level is set to INFO or higher (INFO, DEBUG) then the
                     output will be streamed. Otherwise, the output will stream no matter what
                     if True and it will not stream no matter what if False.
    """
    OUTPUT_ENCODING = 'utf-8'

    logging.debug('executing on [{0}] [{1}]'.format(container.name, command))

    if stream_output is None:
        log_level = logging.getLogger().getEffectiveLevel()
        stream_output = log_level <= logging.INFO

    exec_instance = container.client.api.exec_create(container.id, command, user=user, workdir=workdir)
    exec_out = container.client.api.exec_start(exec_instance['Id'], stream=stream_output)

    try:
        # Stream output from the executing command. A StopIteration exception is raised
        # by the generator returned by the docker-py API when there is no more output.
        while stream_output:
            out = next(exec_out).decode(OUTPUT_ENCODING)
            logging.error(out)

    except StopIteration:
        logging.debug('done')

    if not stream_output:
        logging.debug(exec_out.decode(OUTPUT_ENCODING))

    return container.client.api.exec_inspect(exec_instance['Id'])['ExitCode']
