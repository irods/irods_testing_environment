# grown-up modules
import logging
import time

# local modules
from . import test_runner

class test_manager:
    """A class that manages a list of tests and `test_runners` for executing tests."""

    def __init__(self, containers, tests, test_type='irods_python_suite'):
        """Constructor for `test_manager`.

        Arguments:
        containers -- list of containers which will be used to construct `test_runner`s
        tests -- list of tests which will run on the `test_runners`
        test_type -- a string representing the name of the class implementing the test_runner
        """
        tr_name = '_'.join(['test_runner', test_type])
        tr = eval('.'.join(['test_runner', tr_name]))
        logging.info('[{}]'.format(tr))
        self.test_runners = [tr(c) for c in containers]

        logging.info('[{}]'.format(tests))
        logging.info('[{}]'.format(str(self)))
        logging.info('[{}]'.format(self.test_runners))

        self.duration = -1

        for i, t in enumerate(tests):
            index = i % len(self.test_runners)

            logging.info('index [{}], test [{}]'.format(index, t))
            self.test_runners[index].add_test(t)

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
        for tr in self.test_runners:
            r = r + tr.result_string()

        if self.return_code() is not 0:
            r = r + 'List of failed tests:\n\t{}\n'.format(' '.join(self.failed_tests()))
            r = r + 'Return code:[{}]\n'.format(self.return_code())

        else:
            r = r + 'All tests passed! :)\n'

        if self.duration > 0:
            hours = int(self.duration / 60 / 60)
            minutes = self.duration / 60 - hours * 60
            r = r + 'time elapsed: [{:9.4}]seconds ([{:4}]hours [{:7.4}]minutes)\n'.format(
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

        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures_to_test_runners = {
                executor.submit(tr.run, fail_fast, **kwargs): tr for tr in self.test_runners
            }

            for f in concurrent.futures.as_completed(futures_to_test_runners):
                tr = futures_to_test_runners[f]

                try:
                    f.result()

                    if tr.rc is 0 and len(tr.failed_tests()) is 0:
                        logging.error('tests completed successfully [{}]'.format(tr.name()))
                    else:
                        logging.error('some tests failed [{}]'.format(tr.name()))

                except Exception as e:
                    logging.error('[{}]: exception raised while running test'.format(tr.name()))
                    logging.error(e)

                    tr.rc = 1

                    if fail_fast: raise

        end_time = time.time()

        self.duration = end_time - start_time
