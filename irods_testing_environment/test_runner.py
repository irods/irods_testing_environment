# grown-up modules
import logging
import time

# local modules
from . import context
from . import execute

class test_runner:
    """A class that manages a list of tests and can execute them on a managed container."""

    def __init__(self, executing_container, tests=None):
        """Constructor for `test_runner`.

        The list of tests is not required to be initialized here. `add_test` will append a
        test to the end of the test list.

        Arguments:
        executing_container -- the container on which tests will be executed
        tests -- optional list of tests to use with this runner
        """
        # TODO: each test runner is tied to a single container... might need to abstract this out later
        self.executor = executing_container
        self.tests = tests or list()
        self.rc = 0

        # When a test completes - whether passing or failing - it will be associated with an
        # epoch timestamp from the time module representing the time it took to pass or fail.
        self.passed = dict()
        self.failed = dict()

        # Start the duration time at -1 to indicate that no tests have run
        self.duration = -1


    def __str__(self):
        """Return a string representation of a map representing the data members."""
        return str({
            'executing_container': self.name(),
            'return_code': self.rc,
            'test_list': self.tests,
            'passed_tests': self.passed_tests(),
            'failed_tests': self.failed_tests(),
            'duration': self.duration
        })


    def add_test(self, test):
        """Append `test` to the test list and return self."""
        logging.info('before [{}]'.format(self))
        self.tests.append(test)
        logging.info('after  [{}]'.format(self))
        return self


    def name(self):
        """Return the name of the executing container."""
        return self.executor.name


    def test_list(self):
        """Return the list of tests for which this runner is responsible."""
        return self.tests


    def passed_tests(self):
        """Return the list of tests which have been executed and passed."""
        return self.passed


    def failed_tests(self):
        """Return the list of tests which have been executed and failed."""
        return self.failed


    def skipped_tests(self):
        """Return the list of tests which have not been executed."""
        executed_tests = [t for t in self.passed_tests()] + [t for t in self.failed_tests()]
        return list(filter(lambda t: t not in executed_tests, self.test_list()))


    def result_string(self):
        """Return a string representing the results of running the test list."""
        r = '-----\nresults for [{}]\n'.format(self.name())

        r = r + '\tpassed tests:\n'
        for test, duration in self.passed_tests().items():
            duration_str = '{:9.4}'.format(duration)
            r = r + '\t\t[[{:9}]s]\t[{}]\n'.format(duration_str, test)

        r = r + '\tskipped tests:\n'
        for t in self.skipped_tests():
            r = r + '\t\t[{}]\n'.format(t)

        r = r + '\tfailed tests:\n'
        for test, duration in self.failed_tests().items():
            duration_str = '{:9.4}'.format(duration)
            r = r + '\t\t[[{:9}]s]\t[{}]\n'.format(duration_str, test)

        r = r + '\treturn code:[{}]\n'.format(self.rc)

        if self.duration > 0:
            hours = int(self.duration / 60 / 60)
            minutes = self.duration / 60 - hours * 60
            r = r + '\ttime elapsed: [{:9.4}]seconds ([{:4}]hours [{:9.4}]minutes)\n'.format(
                self.duration, hours, minutes)

        r = r + '-----\n'

        return r


    def run(self, fail_fast=True, **kwargs):
        """Execute test list sequentially on executing container.

        Arguments:
        fail_fast -- if True, the first test to fail ends the run
        **kwargs -- keyword arguments for the specific `test_runner` implementation
        """
        run_start = time.time()

        for t in self.tests:
            start = time.time()

            cmd, ec = self.execute_test(t, **kwargs)

            end = time.time()

            duration = end - start

            if ec is 0:
                self.passed_tests()[t] = duration
                logging.error('[{}]: cmd succeeded [{}]'.format(self.name(), cmd))

            else:
                self.rc = ec
                self.failed_tests()[t] = duration
                logging.error('[{}]: cmd failed [{}] [{}]'.format(self.name(), ec, cmd))

                if fail_fast:
                    raise RuntimeError('[{}]: command failed [{}]'.format(self.name(), cmd))

        run_end = time.time()

        self.duration = run_end - run_start

        if self.rc is not 0:
            logging.error('[{}]: tests that failed [{}]'.format(self.name(), self.failed_tests()))


    def execute_test(self, test, **kwargs):
        """Execute `test` with return the command run and the return code."""
        raise NotImplementedError('test_runner is a base class and should not be used directly')


class test_runner_irods_python_suite(test_runner):
    def __init__(self, executing_container, tests=None):
        super(test_runner_irods_python_suite, self).__init__(executing_container, tests)


    @staticmethod
    def run_tests_command(container):
        """Return a list of strings used as a space-delimited invocation of the test runner."""
        from . import container_info
        return [container_info.python(container), context.run_tests_script()]


    def execute_test(self, test, options=None):
        """Execute `test` with `options` and return the command run and the return code.

        Arguments:
        test -- name of the test to execute
        options -- list of strings which will be appended to the command to execute
        """
        cmd = self.run_tests_command(self.executor) + ['--run_specific_test', test]
        if options: cmd.extend(options)
        return cmd, execute.execute_command(self.executor,
                                            ' '.join(cmd),
                                            user='irods',
                                            workdir=context.irods_home())


class test_runner_irods_unit_tests(test_runner):
    def __init__(self, executing_container, tests=None):
        super(test_runner_irods_unit_tests, self).__init__(executing_container, tests)


    def execute_test(self, test, reporter='junit'):
        """Execute `test` and return the command run and the return code.

        Arguments:
        test -- name of the test to execute
        reporter -- Catch2 reporter to use (options: console, compact, junit, xml)
        """
        import os

        output_dir = os.path.join(context.irods_home(), 'log')
        output_path = os.path.join(output_dir, f'{test}_{reporter}_report.out')

        cmd = [os.path.join(context.unit_tests(), test),
               '--reporter', reporter,
               '--out', output_path]
        return cmd, execute.execute_command(self.executor,
                                            ' '.join(cmd),
                                            user='irods',
                                            workdir=context.irods_home())
