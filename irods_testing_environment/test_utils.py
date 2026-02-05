# grown-up modules
import datetime
import errno
import logging
import os
import tempfile
import uuid

# local modules
from . import container_info, context, execute, test_manager


def job_name(project_name, prefix=None, unique=False):
    """
    Construct unique job name based on the Docker Compose project name.

    Arguments:
        project_name: Docker Compose project name which identifies the type of test being run.
        prefix: Optional prefix for the job name.
        unique: If True, appends a UUID to the job name.

    Returns:
        A job name with the following components, separated by underscores:
            - prefix string (only included if prefix is a non-empty string)
            - project_name
            - current UTC timestamp in ISO-8601 format
            - uuid.uuid4() (as a string; only included if unique is True)
    """
    timestamp = datetime.datetime.now(tz=datetime.timezone.utc).isoformat()
    name = f"{project_name}_{timestamp}"
    if unique:
        name = f"{name}_{uuid.uuid4()!s}"
    return f"{prefix}_{name}" if prefix else name


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

def run_unit_tests(containers, test_list=None, fail_fast=True):
    """Run a set of tests from the python test suite for iRODS.

    Arguments:
    containers -- target containers on which the tests will run
    test_list -- a list of strings of the tests to be run
    options -- list of strings representing script options to pass to the run_tests.py script
    fail_fast -- if True, stop running after first failure; else, runs all tests
    """
    tests = test_list or get_unit_test_list(containers[0])

    tm = test_manager.test_manager(containers, tests, test_type='irods_unit_tests')

    try:
        tm.run(fail_fast)

    finally:
        logging.error(tm.result_string())

    return tm.return_code()


def run_plugin_tests(containers,
                     plugin_name,
                     path_to_test_hook_on_host=None,
                     test_list=None,
                     options=None,
                     fail_fast=True):
    """Run a set of tests from the test hook for the specified iRODS plugin.

    Arguments:
    containers -- target containers on which the tests will run
    plugin_name -- name of the git repo hosting the plugin test hook
    path_to_test_hook_on_host -- local filesystem path on host machine to test hook
    test_list -- a list of strings of the tests to be run
    options -- list of strings representing script options to pass to the run_tests.py script
    fail_fast -- if True, stop running after first failure; else, runs all tests
    """
    tm = test_manager.test_manager(containers, test_list, test_type='irods_plugin_tests')

    try:
        tm.run(fail_fast,
               plugin_repo_name=plugin_name,
               plugin_branch=None,
               path_to_test_hook_on_host=path_to_test_hook_on_host,
               options=options)

    finally:
        logging.error(tm.result_string())

    return tm.return_code()


def run_specific_tests(containers, test_list=None, options=None, fail_fast=True):
    """Run a set of tests from the python test suite for iRODS.

    Arguments:
    containers -- target containers on which the tests will run
    test_list -- a list of strings of the tests to be run
    options -- A list of lists of strings representing options to pass to the scripts running tests
    fail_fast -- if True, stop running after first failure; else, runs all tests
    """
    tests = test_list or get_test_list(containers[0])

    tm = test_manager.test_manager(containers, tests)

    try:
        tm.run(fail_fast, options=options)

    finally:
        logging.error(tm.result_string())

    return tm.return_code()


def run_python_test_suite(container, options=None):
    """Run the entire python test suite for iRODS.

    Arguments:
    container -- target container on which the test script will run
    options -- list of strings representing script options to pass to the run_tests.py script
    """
    command = [container_info.python(container),
               context.run_tests_script(),
               '--run_python_suite']

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


def get_unit_test_list(container):
    """Return list of unit tests extracted from unit_tests_list.json file in `container`.

    Arguments:
    container -- target container from which test list will be extracted
    """
    from . import json_utils
    return json_utils.get_json_from_file(container,
                                         os.path.join(
                                             context.unit_tests(),
                                             'unit_tests_list.json')
                                         )


def get_test_list(container):
    """Return list of tests extracted from core_tests_list.json file in `container`.

    Arguments:
    container -- target container from which test list will be extracted
    """
    from . import json_utils
    return json_utils.get_json_from_file(container,
                                         os.path.join(
                                             context.irods_home(),
                                             'scripts',
                                             'core_tests_list.json')
                                         )
