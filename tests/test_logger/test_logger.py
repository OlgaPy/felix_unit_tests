"""
Unit tests for "logger.logger" module
"""

import unittest
from unittest.mock import MagicMock, patch

from logger import LogLevels, Logger


class TestLogLevels(unittest.TestCase):
    """
    tests for LogLevels class
    """

    def test_has_log_levels_attrs(self):
        """
        Tests that class variables for
        log levels "sys", "warning", "failure"
        and "success" are defined
        """
        self.assertEqual('sys', LogLevels.sys)
        self.assertEqual('warning', LogLevels.warning)
        self.assertEqual('failure', LogLevels.failure)
        self.assertEqual('success', LogLevels.success)


class TestLogger(unittest.TestCase):
    """
    Base class for Logger tests
    """

    def setUp(self) -> None:
        self.name = 'name'
        self.printer = MagicMock()
        self.random_kwargs = {'key1': 'value1', 'key2': 'value2'}
        self.logger = Logger(self.name, self.printer, **self.random_kwargs)


class TestInit(TestLogger):
    """
    Tests for "__init__" method
    """

    def test_sets_instance_name_to_passed_name(self):
        """
        Tests that Logger instance "name"
        attribute is equal to passed to
        constructor "name" argument
        """
        self.assertEqual(self.name, self.logger.name)

    def test_sets_instance_printer_to_passed_printer(self):
        """
        Tests that Logger instance "printer"
        attribute is the same object as passed
        to constructor "printer" argument
        """
        self.assertIs(self.printer, self.logger.printer)

    def test_format_strings_values(self):
        """
        Tests that values for output formatting
        strings are correct
        """
        self.assertEqual('\033[1m', self.logger._format_bold)
        self.assertEqual('\033[4m', self.logger._format_underline)
        self.assertEqual('\033[90m', self.logger._format_color_grey)
        self.assertEqual('\033[91m', self.logger._format_color_red)
        self.assertEqual('\033[92m', self.logger._format_color_green)
        self.assertEqual('\033[93m', self.logger._format_color_yellow)
        self.assertEqual('\033[94m', self.logger._format_color_azure)
        self.assertEqual('\033[95m', self.logger._format_color_pink)
        self.assertEqual('\033[96m', self.logger._format_color_teal)
        self.assertEqual('\033[97m', self.logger._format_color_black)
        self.assertEqual('\033[0m', self.logger._format_end)

    def test_info_string(self):
        """
        Tests that instance "info" attribute
        has correct format
        """
        self.assertEqual(
            f"[{'|'.join([str(x) for x in self.random_kwargs.values()] + [self.name])}]",
            self.logger._info
        )


@patch('sys.exc_info')
@patch('builtins.print')
@patch('datetime.datetime')
class TestWrite(TestLogger):
    """
    Tests for "write" method
    """
    def setUp(self) -> None:
        super(TestWrite, self).setUp()
        self.msg = 'message'

    def test_prints_formatted_message(self, datetime_mock, print_mock, exc_info_mock):
        """
        Tests that passed message is being
        formatted and printed
        """
        self.logger.write(self.msg)
        print_mock.assert_called_once_with(
            f"{self.logger._format_color_yellow}{datetime_mock.now.return_value.replace.return_value} "
            f"{self.logger._info} >>> {self.msg}{self.logger._format_end}")
        datetime_mock.now.return_value.replace.assert_called_once_with(microsecond=0)
        print_mock.reset_mock()
        datetime_mock.now.return_value.replace.reset_mock()

        #############################

        self.logger.write(self.msg, level=LogLevels.warning)
        print_mock.assert_called_once_with(
            f"{self.logger._format_color_azure}{datetime_mock.now.return_value.replace.return_value} "
            f"{self.logger._info} >>> [WARNING] {self.msg}{self.logger._format_end}")
        datetime_mock.now.return_value.replace.assert_called_once_with(microsecond=0)
        print_mock.reset_mock()
        datetime_mock.now.return_value.replace.reset_mock()

        #############################

        self.logger.write(self.msg, level=LogLevels.failure)
        print_mock.assert_called_once_with(
            f"{self.logger._format_color_red}{datetime_mock.now.return_value.replace.return_value} "
            f"{self.logger._info} >>> [FAILURE] {self.msg}{self.logger._format_end}")
        datetime_mock.now.return_value.replace.assert_called_once_with(microsecond=0)
        print_mock.reset_mock()
        datetime_mock.now.return_value.replace.reset_mock()

        #############################

        self.logger.write(self.msg, level=LogLevels.success)
        print_mock.assert_called_once_with(
            f"{self.logger._format_color_green}{datetime_mock.now.return_value.replace.return_value} "
            f"{self.logger._info} >>> [SUCCESS] {self.msg}{self.logger._format_end}")
        datetime_mock.now.return_value.replace.assert_called_once_with(microsecond=0)
        print_mock.reset_mock()
        datetime_mock.now.return_value.replace.reset_mock()

    def test_calls_printer_write_with_formatted_message(self, datetime_mock, print_mock, exc_info_mock):
        """
        Tests that passed message is being
        formatted passed to printer's
        write method
        """
        self.logger.write(self.msg)
        self.printer.write.assert_called_once_with(f'{self.logger._info} >>> {self.msg}')
        self.printer.write.reset_mock()

        #############################

        self.logger.write(self.msg, level=LogLevels.warning)
        self.printer.write.assert_called_once_with(f'{self.logger._info} >>> [WARNING] {self.msg}')
        self.printer.write.reset_mock()

        #############################

        self.logger.write(self.msg, level=LogLevels.failure)
        self.printer.write.assert_called_once_with(f'{self.logger._info} >>> [FAILURE] {self.msg}')
        self.printer.write.reset_mock()

        #############################

        self.logger.write(self.msg, level=LogLevels.success)
        self.printer.write.assert_called_once_with(f'{self.logger._info} >>> [SUCCESS] {self.msg}')
        self.printer.write.reset_mock()

    @patch('traceback.extract_tb')
    def test_adds_traceback_to_msg_if_log_traceback_is_true(
            self, extract_tb_mock, datetime_mock, print_mock, exc_info_mock):
        """
        Tests that if "log_traceback" flag
        is set, traceback info is being logged
        """
        error_value = 'error_value'
        error_traceback = 'error_traceback'
        exc_info_mock.return_value = (None, error_value, error_traceback)
        extracted_traceback = ('error1', 'error2', 'error3')
        extract_tb_mock.return_value = extracted_traceback
        self.logger.write(self.msg, log_traceback=True)

        #############################

        self.printer.write.assert_called_once_with(
        f'{self.logger._info} >>> {self.msg} Error Value: {error_value}; TraceBack: {extracted_traceback[-1]}')
        extract_tb_mock.assert_called_once_with(error_traceback)
