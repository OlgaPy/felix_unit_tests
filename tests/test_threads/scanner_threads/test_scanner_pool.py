from datetime import datetime, timedelta
import unittest
from unittest.mock import MagicMock, patch

from threads.threads_scanner.pool_scanner import PoolScanner


class TestPoolScanner(unittest.TestCase):
    """
    Base class for "PoolScanner" tests.
    """

    def setUp(self) -> None:
        """Set up test."""
        self.target = 'Some Value'
        self.scanner = MagicMock()
        self.scanner.target = self.target
        self.gc_timeout = 1
        self.pool_scanner = PoolScanner(scanner=self.scanner, gc_timeout=self.gc_timeout)


class TestRunningExistProperty(TestPoolScanner):
    """
    Class for "ProtoPoolScanner.running_exist" property
    """

    def test_running_exist_property(self):
        """Test property execution."""
        self.pool_scanner._observer = MagicMock()

        result = self.pool_scanner.running_exist

        self.assertTrue(self.pool_scanner._observer.called)
        self.assertEqual(result, False)


class TestReportProperty(TestPoolScanner):
    """
    Class for "ProtoPoolScanner.report" property
    """

    def test_report_property_with_thread_in_present_status_in_pool(self):
        """Test when self._pool is not empty."""
        self.pool_scanner._observer = MagicMock()
        thread_ip = '127.0.0.12'
        thread_mac = 'AA:BB:CC:CC:CC:DD'
        thread_mbd_id = 27
        self.pool_scanner._pool = [
            MagicMock(ip=thread_ip, mac=thread_mac, mbd_id=thread_mbd_id, present=True)
        ]

        result = self.pool_scanner.report

        self.assertTrue(self.pool_scanner._observer.called)
        self.assertEqual(self.pool_scanner._pool[0].processed, True)
        self.assertEqual(result[0].ip, thread_ip)
        self.assertEqual(result[0].mac, thread_mac)
        self.assertEqual(result[0].mbd_id, thread_mbd_id)

    def test_report_property_with_thread_not_in_present_status_in_pool(self):
        """Test when self._pool is empty."""
        self.pool_scanner._observer = MagicMock()
        thread_ip = '127.0.0.12'
        thread_mac = 'AA:BB:CC:CC:CC:DD'
        thread_server_id = 27
        self.pool_scanner._pool = [
            MagicMock(ip=thread_ip, mac=thread_mac, server_id=thread_server_id, present=False)
        ]

        result = self.pool_scanner.report

        self.assertTrue(self.pool_scanner._observer.called)
        self.assertEqual(self.pool_scanner._pool[0].processed, True)
        self.assertEqual(result, [])


class TestWatchDog(TestPoolScanner):
    """
    Class for "ProtoPoolScanner._observer" method
    """

    @patch('threads.threads_scanner.pool_scanner.gc.collect')
    def test__observer_when_pool_is_not_empty(self, mocked_gc_collect):
        """Test method when self._pool is not empty."""
        test_thread_processed = MagicMock(
            ip='127.0.0.21',
            mac='AA:BB:CC:CC:CC:DD',
            server_id=27,
            processed=True)
        test_thread_not_processed = MagicMock(
            ip='127.0.0.22',
            mac='AA:BB:CC:CC:CC:DF',
            server_id=28)
        self.pool_scanner._pool = [test_thread_processed, test_thread_not_processed]

        self.pool_scanner._observer()

        self.assertEqual(self.pool_scanner._pool, [test_thread_not_processed])
        self.assertTrue(datetime.now() - self.pool_scanner._gc_last_time < timedelta(seconds=10))
        self.assertTrue(mocked_gc_collect.called)

    @patch('threads.threads_scanner.pool_scanner.gc.collect')
    def test__observer_when_new_gc_is_not_allowed(self, mocked_gc_collect):
        """Test method when new gc is not allowed."""
        self.pool_scanner._gc_last_time = \
            datetime.now() - timedelta(seconds=int(self.pool_scanner._gc_timeout / 2))

        self.pool_scanner._observer()

        self.assertFalse(mocked_gc_collect.called)


class TestStartMethod(TestPoolScanner):
    """
    Class for "ProtoPoolScanner._start" method
    """

    def test_start_method_when_pool_is_not_empty(self):
        """Test method when self._pool is not empty."""
        test_thread_1 = MagicMock(ip='127.0.0.21', mac='AA:BB:CC:CC:CC:DD', server_id=27)
        test_thread_2 = MagicMock(ip='127.0.0.22', mac='AA:BB:CC:CC:CC:DF', server_id=28)
        self.pool_scanner._pool = [test_thread_1, test_thread_2]

        self.pool_scanner._start(test_thread_2.ip, test_thread_2.mac)

        self.assertFalse(test_thread_1.start.called)
        self.assertTrue(test_thread_2.start.called)

    def test_start_method_when_pool_is_empty(self):
        """Test method when self._pool is empty."""
        self.pool_scanner._start('127.0.0.21', 'AA:BB:CC:CC:CC:DD')

        self.assertFalse(self.pool_scanner._pool, [])


class TestExistMethod(TestPoolScanner):
    """
    Class for "ProtoPoolScanner._exist" method
    """

    def test_exists_method(self):
        """Test method successful execution."""
        self.pool_scanner._observer = MagicMock()
        thread_ip = '127.0.0.12'
        thread_mac = 'AA:BB:CC:CC:CC:DD'

        result = self.pool_scanner._exist(thread_ip, thread_mac)

        self.assertTrue(self.pool_scanner._observer.called)
        self.assertEqual(result, False)


class TestKillMethod(TestPoolScanner):
    """
    Class for "ProtoPoolScanner.kill" method
    """

    def test_kill_method_when_exist_is_true(self):
        """Test when address exists."""
        self.pool_scanner._exist = MagicMock(return_value=True)

        test_thread_1 = MagicMock(ip='127.0.0.21', mac='AA:BB:CC:CC:CC:DD', server_id=27)
        test_thread_2 = MagicMock(ip='127.0.0.22', mac='AA:BB:CC:CC:CC:DF', server_id=28)
        self.pool_scanner._pool = [test_thread_1, test_thread_2]

        self.pool_scanner.kill(test_thread_2.ip, test_thread_2.mac)

        self.assertTrue(self.pool_scanner._exist.called)
        self.assertEqual(self.pool_scanner._pool, [test_thread_1])

    def test_kill_method_when_exist_is_false(self):
        """Test when address not exists."""
        self.pool_scanner._exist = MagicMock(return_value=False)

        test_thread_1 = MagicMock(ip='127.0.0.21', mac='AA:BB:CC:CC:CC:DD', server_id=27)
        test_thread_2 = MagicMock(ip='127.0.0.22', mac='AA:BB:CC:CC:CC:DF', server_id=28)
        self.pool_scanner._pool = [test_thread_1, test_thread_2]

        self.pool_scanner.kill('127.0.0.11', 'AA:BB:CC:CC:CC:0F')

        self.assertTrue(self.pool_scanner._exist.called)
        self.assertEqual(self.pool_scanner._pool, [test_thread_1, test_thread_2])

    def test_kill_method_when_exist_is_true_but_pool_is_empty(self):
        """Test when address exists but self._pool is empty."""
        self.pool_scanner._exist = MagicMock(return_value=True)
        self.pool_scanner._pool = []

        self.pool_scanner.kill('127.0.0.11', 'AA:BB:CC:CC:CC:0F')

        self.assertTrue(self.pool_scanner._exist.called)
