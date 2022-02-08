# grown-up modules
import logging
import os
import tempfile

# local modules
from . import archive
from . import context
from . import execute
from . import services
from .install import install

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


def run_specific_tests(containers, tests, options=None, fail_fast=True):
    """Run a set of tests from the python test suite for iRODS.

    Arguments:
    containers -- target containers on which the tests will run
    tests -- a list of strings of the tests to be run
    options -- list of strings representing script options to pass to the run_tests.py script
    fail_fast -- if True, stop running after first failure; else, runs all tests
    """
    import concurrent.futures

    def run_specific_test(options, tests, container, fail_fast):
        command = ['python', path_to_run_tests_script()]

        if options: command.extend(options)

        rc = 0
        failed_tests = list()

        for test in tests:
            cmd = command + ['--run_specific_test', test]
            ec = execute.execute_command(container,
                                         ' '.join(cmd),
                                         user='irods',
                                         workdir=context.irods_home(),
                                         stream_output=True)

            if ec is not 0:
                rc = ec
                failed_tests.append(test)
                last_command_to_fail = cmd
                logging.warning('[{}]: command exited with error code [{}] [{}] [{}]'
                                .format(container.name, ec, cmd, container.name))

                if fail_fast:
                    logging.critical('[{}]: command failed [{}]'.format(container.name, cmd))
                    break

        if rc is not 0:
            logging.error('[{}]: last command to fail [{}]'.format(container.name, last_command_to_fail))
            logging.error('[{}]: tests that failed [{}]'.format(container.name, failed_tests))

        return (rc, failed_tests)

    test_lists = {
        c.name: {
            'tests': list(),
            'rc': 0,
            'failures': list()
        }
        for c in containers
    }
    keys = list(test_lists.keys())

    logging.info('keys [{}], tests [{}]'.format(keys, tests))

    # Evenly distribute the tests amongst the containers. The -1 is to avoid going beyond the
    # end of the list of keys since it is 0-indexed.
    i = 0
    for t in tests:
        logging.debug('test_lists [{}]'.format(test_lists))
        logging.debug('index [{}], test [{}]'.format(i % len(keys), t))
        test_lists[keys[i % len(keys)]]['tests'].append(t)
        i = i + 1

    logging.info('test_lists [{}]'.format(test_lists))

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures_to_containers = {
            executor.submit(
                run_specific_test,
                options, test_lists[c.name]['tests'], c, fail_fast
            ): c for c in containers
        }

        for f in concurrent.futures.as_completed(futures_to_containers):
            container = futures_to_containers[f]

            try:
                rc, failed_tests = f.result()
                if rc is 0 and len(failed_tests) is 0:
                    logging.warning('tests completed successfully [{}]'.format(container.name))
                else:
                    logging.warning('some tests failed [{}]'.format(container.name))

                test_lists[container.name]['rc'] = rc
                test_lists[container.name]['failures'] = failed_tests

            except Exception as e:
                logging.error('exception raised while running iRODS tests [{}]'
                              .format(container.name))
                logging.error(e)

                test_lists[container.name]['rc'] = 1

    rc = 0
    for c in containers:
        # TODO: it's not really an error, I just want to make sure it gets shown
        logging.error('-----\nresults for [{}]'.format(c.name))
        logging.error('\ttests run:')
        for t in test_lists[c.name]['tests']:
            logging.error('\t\t[{}]'.format(t))
        logging.error('\tfailed tests:')
        for f in test_lists[c.name]['failures']:
            logging.error('\t\t[{}]'.format(f))
        ec = test_lists[c.name]['rc']
        if ec is not 0:
            rc = ec
        logging.error('\treturn code:[{}]\n-----\n'.format(ec))

    return rc

def run_python_test_suite(container, options=None):
    """Run the entire python test suite for iRODS.

    Arguments:
    container -- target container on which the test script will run
    options -- list of strings representing script options to pass to the run_tests.py script
    """
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


def run_test_hook(container, repo_name, branch=None, options=None):
    """Run the test hook from the specified git repository.

    Arguments:
    container -- target container on which the test script will run
    repo_name -- name of the git repo
    branch -- name of the branch to checkout in cloned git repo
    options -- list of strings representing script options to pass to the run_tests.py script
    """
    repo_path = services.clone_repository_to_container(container, repo_name, branch=branch)

    # TODO: option?
    path_to_test_hook = os.path.join(repo_path,
                                     'irods_consortium_continuous_integration_test_hook.py')

    return run_test_hook_file_in_container(container, path_to_test_hook, options)


def run_test_hook_file(container, path_to_test_hook_on_host, options=None):
    """Run the local test hook in the container.

    Arguments:
    container -- target container on which the test hook will run
    path_to_test_hook_on_host -- local filesystem path on host machine to test hook
    options -- list of strings representing script options to pass to the run_tests.py script
    """
    f = os.path.abspath(path_to_test_hook_on_host)
    archive.copy_archive_to_container(container, archive.create_archive([f]))
    return run_test_hook_file_in_container(container, f, options)

def run_test_hook_file_in_container(container, path_to_test_hook, options=None):
    """Run the test hook at the specified path in the container.

    Arguments:
    container -- target container on which the test script will run
    path_to_test_hook -- path in the container for the test hook file
    options -- list of strings representing script options to pass to the run_tests.py script
    """
    install.install_pip_package_from_repo(container, 'irods_python_ci_utilities')

    command = ['python', path_to_test_hook]

    if options: command.extend(options)

    ec = execute.execute_command(container,
                                 ' '.join(command),
                                 stream_output=True)

    if ec is not 0:
        logging.warning('command exited with error code [{}] [{}] [{}]'
                        .format(ec, command, container.name))

    return ec


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

