# grown-up modules
import logging

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
        self.passed = list()
        self.failed = list()
        self.rc = 0


    def __str__(self):
        """Return a string representation of a map representing the data members."""
        return str({
            'executing_container': self.name(),
            'return_code': self.rc,
            'test_list': self.tests,
            'passed_tests': self.passed_tests(),
            'failed_tests': self.failed_tests()
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
        executed_tests = self.passed_tests() + self.failed_tests()
        return list(filter(lambda t: t not in executed_tests, self.test_list()))


    def result_string(self):
        """Return a string representing the results of running the test list."""
        r = '-----\nresults for [{}]\n'.format(self.name())

        r = r + '\tpassed tests:\n'
        for t in self.passed_tests():
            r = r + '\t\t[{}]\n'.format(t)

        r = r + '\tskipped tests:\n'
        for t in self.skipped_tests():
            r = r + '\t\t[{}]\n'.format(t)

        r = r + '\tfailed tests:\n'
        for t in self.failed_tests():
            r = r + '\t\t[{}]\n'.format(t)

        r = r + '\treturn code:[{}]\n-----\n'.format(self.rc)

        return r


    def run(self, fail_fast=True, *args):
        """Execute test list sequentially on executing container.

        Arguments:
        fail_fast -- if True, the first test to fail ends the run
        *args -- any additional arguments that the test execution can take
        """
        for t in self.tests:
            cmd, ec = self.execute_test(t, *args)

            if ec is 0:
                self.passed_tests().append(t)
                logging.info('[{}]: cmd succeeded [{}]'.format(self.name(), cmd))

            else:
                self.rc = ec
                self.failed_tests().append(t)
                logging.warning('[{}]: cmd failed [{}] [{}]'.format(self.name(), ec, cmd))

                if fail_fast:
                    raise RuntimeError('[{}]: command failed [{}]'.format(self.name(), cmd))

        if self.rc is not 0:
            logging.error('[{}]: tests that failed [{}]'.format(self.name(), self.failed_tests()))


    def execute_test(self, test, *args):
        """Execute `test` with return the command run and the return code."""
        raise NotImplementedError('test_runner is a base class and should not be used directly')


class test_runner_irods_python_suite(test_runner):
    def __init__(self, executing_container, tests=None):
        super(test_runner_irods_python_suite, self).__init__(executing_container, tests)


    @staticmethod
    def run_tests_command():
        """Return a list of strings used as a space-delimited invocation of the test runner."""
        return [context.python(), context.run_tests_script()]


    def execute_test(self, test, options=None):
        """Execute `test` with `options` and return the command run and the return code."""
        cmd = self.run_tests_command() + ['--run_specific_test', test]
        if options: cmd.append(options)
        return cmd, execute.execute_command(self.executor,
                                            ' '.join(cmd),
                                            user='irods',
                                            workdir=context.irods_home(),
                                            stream_output=True)
