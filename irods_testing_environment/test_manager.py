# grown-up modules
import logging
import queue
import time

# local modules
from . import test_runner

class test_manager:
    """A class that manages a list of tests and `test_runners` for executing tests."""

    def __init__(self, containers, tests, test_type='irods_python_suite'):
        """Constructor for `test_manager`.

        A note about passing `None` to `tests`:
        `None` is a special value which indicates that no test list was specified. The test
        runner implementations should have behavior defined for this case. The intended use
        is to use the "default" behavior of the script running the tests (i.e. no specific
        test is passed to the script). The test_manager and test_runners do not have control
        over how the tests are run at this point, so we must fall back to using one executor
        regardless of how many exist. The other executors will have empty test lists.

        Arguments:
        containers -- list of containers which will be used to construct `test_runner`s
        tests -- list of tests which will run on the `test_runners`
        test_type -- a string representing the name of the class implementing the test_runner
        """
        tr_name = '_'.join(['test_runner', test_type])
        tr = eval('.'.join(['test_runner', tr_name]))
        logging.info('[{}]'.format(tr))
        self.test_runners = [tr(c) for c in containers]
        self.test_list = tests

        logging.info('[{}]'.format(tests))
        logging.info('[{}]'.format(str(self)))
        logging.info('[{}]'.format(self.test_runners))

        self.duration = -1

        logging.info('[{}]'.format(str(self)))


    def __str__(self):
        """Return a string representation of the list of `test_runners`."""
        return str([str(tr) for tr in self.test_runners])


    def failed_tests(self):
        """Return a list of failed tests across the managed `test_runners`."""
        return [t for tr in self.test_runners for t in tr.failed_tests()]


    def return_code(self):
        """Return int representing the 'overall' return code from a test run.

        Return 0 if all `test_runners` have a return code of 0. Otherwise, 1.
        """
        logging.info('[{}]'.format([tr.rc for tr in self.test_runners]))
        return 0 if [tr.rc for tr in self.test_runners].count(0) == len(self.test_runners) else 1


    def result_string(self):
        """Return string showing tests that passed and failed from each `test_runner.`"""
        r = '==== begin test run results ====\n'
        tests_were_skipped = False
        for tr in self.test_runners:
            r = r + tr.result_string()
            tests_were_skipped = tests_were_skipped if tests_were_skipped else len(tr.skipped_tests()) > 0

        if self.return_code() is not 0:
            r = r + 'List of failed tests:\n\t{}\n'.format(' '.join([t or 'all tests' for t,_ in self.failed_tests()]))
            r = r + 'Return code:[{}]\n'.format(self.return_code())

        elif tests_were_skipped:
            r = r + 'Some tests were skipped or did not complete...\n'

        else:
            r = r + 'All tests passed! :)\n'

        if self.duration > 0:
            hours = int(self.duration / 60 / 60)
            minutes = self.duration / 60 - hours * 60
            r = r + 'time elapsed: [{:>9.4f}]seconds ([{:>4d}]hours [{:>7.4f}]minutes)\n'.format(
                    self.duration, hours, minutes)

        r = r + '==== end of test run results ====\n'

        return r


    def run(self, fail_fast=True, **kwargs):
        """Run managed `test_runners` in parallel.

        Arguments:
        fail_fast -- if True, the first test to fail ends the run
        **kwargs -- keyword arguments to be passed to the `test_runner`'s specific `run` method
        """
        import concurrent.futures

        test_queue = queue.Queue()

        if self.test_list is None:
            test_queue.put(None)
        else:
            for t in self.test_list:
                test_queue.put(t)

        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures_to_test_runners = {
                executor.submit(tr.run, test_queue, fail_fast, **kwargs): tr for tr in self.test_runners
            }

            for f in concurrent.futures.as_completed(futures_to_test_runners):
                tr = futures_to_test_runners[f]

                try:
                    f.result()

                    if tr.rc is 0 and len(tr.failed_tests()) is 0:
                        logging.error(f'[{tr.name()}]: tests completed successfully')
                    else:
                        logging.error(f'[{tr.name()}]: some tests failed')

                except Exception as e:
                    logging.error(f'[{tr.name()}]: exception raised while running test')
                    logging.error(e)

                    tr.rc = 1

                    if fail_fast: raise

        end_time = time.time()

        self.duration = end_time - start_time
