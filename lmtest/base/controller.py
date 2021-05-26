"""Module containing test controller class."""
import argparse
import os
import sys
from tempfile import gettempdir
from time import sleep

from lmtest.base.daemon import Daemon, DaemonCommands
from lmtest.base.test_base import LmTest, LmTestFailure, LmTestWarning
from lmtest.notifications.console_notifier import ConsoleNotifier
from lmtest.notifications.log_notifier import LogNotifier


CONTROLLER_PID_FILE = os.path.join(gettempdir(), 'controller.pid')
DEFAULT_SLEEP_TIME = 10


# .............................................................................
class Controller(Daemon):
    """Test controller."""

    _tests = []

    # .............................
    def initialize(self):
        """Initialize the test controller."""
        # self._tests = []
        self._success_count = 0
        self._warn_count = 0
        self._fail_count = 0
        self.notifier = ConsoleNotifier()

    # .............................
    def add_tests(self, new_tests):
        """Add a new test object to run.

        Args:
            new_tests (`list` of `LmTest`): A list of test objects to run.
        """
        if isinstance(new_tests, LmTest):
            new_tests = [new_tests]
        self._tests.extend(new_tests)
        self._tests.sort()

    # .............................
    def rest(self, sleep_seconds=DEFAULT_SLEEP_TIME):
        """Sleep before trying to run the next test.

        Note: This is abstracted just a bit in case we want to sleep for
            "smart" intervals, such as until the next test is scheduled to run.

        Args:
            sleep_seconds (`int`, optional): The number of seconds to sleep.
        """
        print('Test controller sleeping for {} seconds...'.format(sleep_seconds))
        sleep(sleep_seconds)
        for test in self._tests:
            test.delay_time -= sleep_seconds

    # .............................
    def run(self):
        """Run the test controller until told to stop."""
        print('Running Test Controller')
        try:
            while self.keep_running and os.path.exists(self.pidfile):
                # Get the first test if it exists and run it
                if len(self._tests) > 0 and self._tests[0].delay_time <= 0:
                    next_test = self._tests.pop(0)
                    self.run_test(next_test)
                # Sleep
                self.rest()
        except Exception as err:
            self.log.error('An error occurred with the test controller')
            self.log.error(err)

    # .............................
    def run_test(self, test_to_run):
        """Run a test and process the result.

        Args:
            test_to_run (`LmTest`): The test that should be run.
        """
        notify_message = None
        try:
            # Tell the test to run
            print('  - Running test: {}'.format(test_to_run))
            test_to_run.run_test()
            self._success_count += 1
            notify_message = '    - PASS'
        except LmTestWarning as lm_warn:
            notify_message = '    - WARNING: {}'.format(str(lm_warn))
            self._warn_count += 1
            self.notifier.notifiy_warning(notify_message)
        except LmTestFailure as lm_fail:
            notify_message = '    - FAILURE: {}'.format(str(lm_fail))
            self._fail_count += 1
            self.notifier.notify_failure(notify_message)
        # if notify_message:
        #     # Send notification
        #     print(notify_message)

        if test_to_run.get_new_tests():
            self.add_tests(test_to_run.get_new_tests())

    # .............................
    def set_notifier(self, notifier):
        """Set the Controller instances notification method.

        Args:
            notifier (Notifier): The notifier to use for this instance.
        """
        self.notifier = notifier


# .............................................................................
def main():
    """Run the script."""
    parser = argparse.ArgumentParser(
        prog='Lifemapper Makeflow Daemon (Matt Daemon)',
        description='Controls a pool of Makeflow processes',
    )

    parser.add_argument(
        '-l', '--log_file', type=str,
        help='File path to log notifications to.  Use console if not provided.'
    )
    parser.add_argument(
        'cmd',
        choices=[DaemonCommands.START, DaemonCommands.STOP, DaemonCommands.RESTART],
        help='The action that should be performed by the makeflow daemon',
    )

    args = parser.parse_args()

    controller_daemon = Controller(CONTROLLER_PID_FILE)

    if args.cmd.lower() == DaemonCommands.START:
        print('Start')
        # Check to see if notifier configuration is provided
        if args.log_file is not None:
            controller_daemon.set_notifier(LogNotifier(args.log_file))
        controller_daemon.start()
    elif args.cmd.lower() == DaemonCommands.STOP:
        print('Stop')
        controller_daemon.stop()
    elif args.cmd.lower() == DaemonCommands.RESTART:
        controller_daemon.restart()
    else:
        print(('Unknown command: {}'.format(args.cmd.lower())))
        sys.exit(2)


# .............................................................................
if __name__ == "__main__":
    main()