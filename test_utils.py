# grown-up modules
import logging
import os

# local modules
import context
import execute

def path_to_run_tests_script():
    """Return the path to the script which runs the tests."""
    return os.path.join(context.irods_home(), 'scripts', 'run_tests.py')

def job_name(project_name, prefix=None):
    """Construct unique job name based on the docker-compose project name.

    The job name returned will be of the form: `project_name`_`prefix`_`uuid.uuid4()`

    If no `prefix` is provided, the job name will be of the form: `project_name`_`uuid.uuid4()`

    Arguments:
    project_name -- docker-compose project name which identifies the type of test being run
    prefix -- optional prefix for the job name
    """
    import uuid
    # TODO: use timestamps, also
    if prefix:
        return '_'.join([prefix, project_name, str(uuid.uuid4())])

    return '_'.join([project_name, str(uuid.uuid4())])


def make_output_directory(dirname, basename):
    """Create a directory for job output and return its full path.

    Arguments:
    dirname -- base directory in which the unique subdirectory for output will be created
    basename -- unique subdirectory which will be created under the provided dirname
    """
    directory = os.path.join(os.path.abspath(dirname), basename)

    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST or not os.path.isdir(directory):
            raise

    return directory


def run_specific_tests(container, tests, options=None, fail_fast=True):
    # start constructing the run_tests command
    command = ['python', path_to_run_tests_script()]

    if options: command.extend(options)

    rc = 0

    for test in tests:
        cmd = command + ['--run_specific_test', test]
        ec = execute.execute_command(container,
                                     ' '.join(cmd),
                                     user='irods',
                                     workdir=context.irods_home(),
                                     stream_output=True)

        if ec is not 0:
            rc = ec
            last_command_to_fail = cmd
            logging.warning('command exited with error code [{}] [{}] [{}]'
                            .format(ec, cmd, container.name))

            if fail_fast:
                logging.critical('command failed [{}]'.format(cmd))
                break

    if rc is not 0:
        logging.error('last command to fail [{}]'.format(last_command_to_fail))

    return rc


def run_python_test_suite(container, options=None):
    # start constructing the run_tests command
    command = ['python', path_to_run_tests_script(), '--run_python_suite']

    if options: command.extend(options)

    ec = execute.execute_command(container,
                                 ' '.join(command),
                                 user='irods',
                                 workdir=context.irods_home(),
                                 stream_output=True)

    if ec is not 0:
        logging.warning('command exited with error code [{}] [{}] [{}]'
                        .format(ec, command, container.name))

    return ec
