# grown-up modules
import compose.cli.command
import docker
import logging
import os

# local modules
import context

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
            logging.info(next(exec_out).decode(OUTPUT_ENCODING))

    except StopIteration:
        logging.debug('done')

    finally:
        logging.getLogger().setLevel(previous_log_level)

    if not stream_output:
        logging.debug(exec_out.decode(OUTPUT_ENCODING))

    return container.client.api.exec_inspect(exec_instance['Id'])['ExitCode']

if __name__ == "__main__":
    import argparse
    import logs

    parser = argparse.ArgumentParser(description='Run commands on a running container as iRODS service account.')
    parser.add_argument('project_path', metavar='PROJECT_PATH', type=str,
                        help='Path to the docker-compose project on which packages will be installed.')
    parser.add_argument('commands', metavar='COMMANDS', nargs='+',
                        help='Space-delimited list of commands to be run')
    parser.add_argument('--run-on-container', '-t', metavar='TARGET_CONTAINER', dest='run_on', type=str,
                        help='The name of the container on which the command will run. By default, runs on all containers in project.')
    parser.add_argument('--project-name', metavar='PROJECT_NAME', type=str, dest='project_name',
                        help='Name of the docker-compose project on which to install packages.')
    parser.add_argument('--verbose', '-v', dest='verbosity', action='count', default=1,
                        help='Increase the level of output to stdout. CRITICAL and ERROR messages will always be printed.')
    parser.add_argument('--user', '-u', metavar='USER', dest='user', default='root',
                        help='Name of the user to be when executing the commands.')
    parser.add_argument('--workdir', '-w', metavar='WORKING_DIRECTORY', dest='workdir', default='/',
                        help='Working directory for execution of commands.')

    args = parser.parse_args()

    logs.configure(args.verbosity)

    ec = 0
    containers = list()

    docker_client = docker.from_env()

    try:
        p = compose.cli.command.get_project(os.path.abspath(args.project_path), project_name=args.project_name)

        # Get the container on which the command is to be executed
        containers = list()
        if args.run_on:
            containers.append(docker_client.containers.get(args.run_on))
        else:
            containers = p.containers()

        # Serially execute the list of commands provided in the input
        for c in containers:
            if context.is_catalog_database_container(c): continue

            target_container = docker_client.containers.get(c.name)
            for command in args.commands:
                # TODO: on --continue, save only failure ec's/commands
                ec = execute_command(target_container, command, user=args.user, workdir=args.workdir, stream_output=True)

    except Exception as e:
        logging.critical(e)

        raise

    exit(ec)
