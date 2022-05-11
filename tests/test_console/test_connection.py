"""
Unit tests for "console.Connection" class
"""
import socket
import unittest
from unittest.mock import Mock, patch, call, MagicMock

import invoke

import protocols
from console import Connection
from console.exceptions import LoginFailed, CommandFailed, TimeoutExpired


class TestConnection(unittest.TestCase):
    """
    Base class for "Connection" tests
    """

    def setUp(self) -> None:
        """Set up test."""
        with patch('console.connection.logger'):
            self.connection = Connection(
                ip='192.168.140.256',
                login='some_login',
                password='blablabla',
                port=22,
                conn_tm=5,
                exec_tm=10,
                logfile=Mock()
            )


class TestConnectionClass(TestConnection):
    """
    Unit tests for "Connection" class
    """

    def test_subclass_of_console_protocol(self):
        """
        Tests that Connection class is a subclass
        of "protocols.Console"
        """
        ### Assertions ###

        self.assertIs(Connection.__base__, protocols.Console)


@patch('console.connection.settings')
@patch('console.connection.logger')
class TestInit(TestConnection):
    """
    Unit tests for "Connection.__init__" method
    """

    def test_sets_instance_attrs(self, logger_mock, settings_mock):
        """
        Tests that provided arguments values are
        set to instance attributes
        """
        ### Setup ###

        ip_addr = '192.168.140.256'
        login = 'some_login'
        password = 'blablabla'
        port = 80
        conn_tms = (123, None)
        exec_tms = (456, None)
        logfile = Mock()

        ### Run ###

        for conn_tm, exec_tm in zip(conn_tms, exec_tms):
            with self.subTest(
                    conn_tm=conn_tm,
                    exec_tm=exec_tm):
                logger_mock.reset_mock()
                conn = Connection(
                    ip=ip_addr,
                    login=login,
                    password=password,
                    port=port,
                    conn_tm=conn_tm,
                    exec_tm=exec_tm,
                    logfile=logfile
                )

                ### Assertions ###

                self.assertEqual(ip_addr, conn._ip)
                self.assertEqual(login, conn._login)
                self.assertEqual(password, conn._password)
                self.assertEqual(port, conn._port)
                self.assertEqual(conn_tm if conn_tm else settings_mock.SSH.conn_tm,
                                 conn._conn_tm)
                self.assertEqual(exec_tm if exec_tm else settings_mock.SSH.exec_tm,
                                 conn._exec_tm)
                self.assertIs(conn._logger, logger_mock.CustomLogger.return_value)
                logger_mock.CustomLogger.assert_called_once_with(
                    name=Connection.__name__, printer=logfile)
                self.assertIsNone(conn._console)


@patch('console.connection.fabric')
class TestGetConsole(TestConnection):
    """
    Unit tests for "Connection._get_console" method
    """

    def test_creating_console(self, fabric_mock):
        """
        If '_console' attribute is None, "fabric.Console" instance
        should be created, stored in that attribute and returned
        """
        ### Run ###

        result = self.connection._get_console()

        ### Assertions ###

        fabric_mock.Connection.assert_called_once_with(
            host=self.connection._ip,
            login=self.connection._login,
            port=self.connection._port,
            config=fabric_mock.Config.return_value,
            conn_tm=self.connection._conn_tm,
            conn_kwargs={
                'password': self.connection._password,
                'look_for_keys': False,
                'allow_agent': False}
        )
        self.assertIs(self.connection._console, fabric_mock.Connection.return_value)
        self.assertIs(result, fabric_mock.Connection.return_value)

    def test_returns_previously_created_console(self, fabric_mock):
        """
        If "fabric.Connection" instance was created before
        it's being returned and new instance is not being created
        """
        ### Setup ###

        console = Mock()
        self.connection._console = console

        ### Run ###

        result = self.connection._get_console()

        ### Assertions ###

        self.assertIs(result, console)
        fabric_mock.Connection.assert_not_called()
        self.assertIs(self.connection._console, console)


@patch('console.connection.invoke.Responder')
class TestRunCommand(TestConnection):
    """
    Unit tests for "Connection.run_command" method
    """

    def setUp(self) -> None:
        """Set up test."""
        super().setUp()

        self.cmd = 'some command'
        self.timeout = 123
        self.pattern = r'\[sudo\].*:'
        self.localhost_ip = '127.0.0.1'
        self.remote_ip = '192.168.140.256'
        self.console = MagicMock()
        self.console.__enter__.return_value = self.console
        self.connection._get_console = Mock(return_value=self.console)
        self.stdout = '[sudo] password for somebody: \nline 1\nline 2\nline 3'
        self.output = self.stdout.splitlines()[1:]
        self.stderr = 'err line 1\nerr line 2\nerr line 3'
        self.err_output = [f'<stderr>: {line}' for line in self.stderr.splitlines()]
        self.result = Mock(stdout=self.stdout, stderr=self.stderr, exited=0)
        self.console.run.return_value = self.result
        self.console.local.return_value = self.result

    def test_successful_exec(self, responder_mock):
        """Test method successful execution."""
        for ip_address in self.localhost_ip, self.remote_ip:
            for login in 'somebody', 'root':
                for timeout in self.timeout, None:
                    for suppress_logs in False, True:
                        with self.subTest(ip=ip_address, login=login, supress_logs=suppress_logs):
                            ### Setup ###
                            self.console.reset_mock()
                            responder_mock.reset_mock()
                            self.connection._logger.raw_emit.reset_mock()

                            self.connection._ip = ip_address
                            self.connection._login = login

                            cmd = self.cmd if login == 'root' else f'sudo {self.cmd}'

                            ### Run ###

                            result = self.connection.run_command(self.cmd, timeout, suppress_logs)

                            ### Assertions ###

                            if ip_address == self.localhost_ip:
                                self.console.local.assert_called_once_with(
                                    cmd,
                                    pty=True,
                                    hide='both',
                                    watchers=[responder_mock.return_value],
                                    timeout=timeout if timeout else self.connection._exec_tm
                                )
                            elif ip_address == self.remote_ip:
                                self.console.run.assert_called_once_with(
                                    cmd,
                                    pty=True,
                                    hide='both',
                                    watchers=[responder_mock.return_value],
                                    timeout=timeout if timeout else self.connection._exec_tm
                                )
                            responder_mock.assert_called_once_with(
                                pattern=self.pattern, response=f'{self.connection._password}\n')

                            if not suppress_logs:
                                expected_calls = \
                                    [call(f'{login}@{ip_address}:~$ {cmd}')] + \
                                    [call(line) for line in self.output] + \
                                    [call(line) for line in self.err_output] + \
                                    [call(f'{login}@{ip_address}:~$ echo $?'),
                                     call(f'{login}@{ip_address}:~$ {self.result.exited}')]
                                self.assertEqual(
                                    expected_calls,
                                    self.connection._logger.raw_emit.call_args_list)
                            if suppress_logs:
                                self.connection._logger.raw_emit.assert_not_called()

                            self.assertEqual(self.output, result)
                            self.console.__enter__.assert_called_once()
                            self.console.__exit__.assert_called_once()

    def test_bad_exit_code(self, responder_mock):
        """Test console command returned code is not 0."""
        self.result.exited = 1

        for ip_address in self.localhost_ip, self.remote_ip:
            for login in 'somebody', 'root':
                for timeout in self.timeout, None:
                    for suppress_logs in False, True:
                        with self.subTest(ip=ip_address, login=login, supress_logs=suppress_logs):
                            ### Setup ###
                            self.console.reset_mock()
                            responder_mock.reset_mock()
                            self.connection._logger.raw_emit.reset_mock()

                            self.connection._ip = ip_address
                            self.connection._login = login

                            cmd = self.cmd if login == 'root' else f'sudo {self.cmd}'

                            ### Run ###

                            with self.assertRaises(CommandFailed) as context:
                                self.connection.run_command(self.cmd, timeout, suppress_logs)

                            ### Assertions ###

                            self.assertEqual(cmd, context.exception.command)
                            self.assertEqual(self.output, context.exception.output)
                            self.assertEqual(self.stderr.splitlines(), context.exception.err_output)
                            self.assertEqual(self.result.exited, context.exception.exitcode)

                            if ip_address == self.localhost_ip:
                                self.console.local.assert_called_once_with(
                                    cmd,
                                    pty=True,
                                    hide='both',
                                    watchers=[responder_mock.return_value],
                                    timeout=timeout if timeout else self.connection._exec_tm
                                )
                            elif ip_address == self.remote_ip:
                                self.console.run.assert_called_once_with(
                                    cmd,
                                    pty=True,
                                    hide='both',
                                    watchers=[responder_mock.return_value],
                                    timeout=timeout if timeout else self.connection._exec_tm
                                )
                            responder_mock.assert_called_once_with(
                                pattern=self.pattern, response=f'{self.connection._password}\n')

                            if not suppress_logs:
                                expected_calls = [call(f'{login}@{ip_address}:~$ {cmd}')] + \
                                                 [call(line) for line in self.output] + \
                                                 [call(line) for line in self.err_output] + \
                                                 [call(f'{login}@{ip_address}:~$ echo $?'),
                                                  call(f'{login}@{ip_address}:~$ {self.result.exited}')]
                                self.assertEqual(
                                    expected_calls,
                                    self.connection._logger.raw_emit.call_args_list)
                            if suppress_logs:
                                self.connection._logger.raw_emit.assert_not_called()

                            self.console.__enter__.assert_called_once()
                            self.console.__exit__.assert_called_once()

    def test_exec_tm_expired(self, responder_mock):
        """Test method finished with execution timeout of console command is expired."""
        self.result.exited = -1

        for ip_address in self.localhost_ip, self.remote_ip:
            for login in 'somebody', 'root':
                for timeout in self.timeout, None:
                    for suppress_logs in False, True:
                        with self.subTest(ip=ip_address, login=login, supress_logs=suppress_logs):
                            ### Setup ###
                            self.console.reset_mock()
                            responder_mock.reset_mock()
                            self.connection._logger.raw_emit.reset_mock()

                            self.connection._ip = ip_address
                            self.connection._login = login

                            cmd = self.cmd if login == 'root' else f'sudo {self.cmd}'

                            def se(*args, **kwargs):
                                raise invoke.exceptions.CommandTimedOut(self.result, 123)

                            self.console.run.side_effect = se
                            self.console.local.side_effect = se

                            ### Run ###

                            with self.assertRaises(TimeoutExpired) as context:
                                self.connection.run_command(self.cmd, timeout, suppress_logs)

                            ### Assertions ###

                            self.assertEqual(cmd, context.exception.command)
                            self.assertEqual(timeout if timeout else self.connection._exec_tm,
                                             context.exception.timeout)

                            if ip_address == self.localhost_ip:
                                self.console.local.assert_called_once_with(
                                    cmd,
                                    pty=True,
                                    hide='both',
                                    watchers=[responder_mock.return_value],
                                    timeout=timeout if timeout else self.connection._exec_tm
                                )
                            elif ip_address == self.remote_ip:
                                self.console.run.assert_called_once_with(
                                    cmd,
                                    pty=True,
                                    hide='both',
                                    watchers=[responder_mock.return_value],
                                    timeout=timeout if timeout else self.connection._exec_tm
                                )
                            responder_mock.assert_called_once_with(
                                pattern=self.pattern, response=f'{self.connection._password}\n')

                            if not suppress_logs:
                                expected_calls = \
                                    [call(f'{login}@{ip_address}:~$ {cmd}')] + \
                                    [call(line) for line in self.output] + \
                                    [call(line) for line in self.err_output] + \
                                    [call(f'{login}@{ip_address}:~$ echo $?'),
                                     call(f'{login}@{ip_address}:~$ {self.result.exited}')]
                                self.assertEqual(
                                    expected_calls,
                                    self.connection._logger.raw_emit.call_args_list)
                            if suppress_logs:
                                self.connection._logger.raw_emit.assert_not_called()

                            self.console.__enter__.assert_called_once()
                            self.console.__exit__.assert_called_once()

    def test_conn_tm_expired(self, responder_mock):
        """Test method finished with connection timeout expired."""
        for ip_address in self.localhost_ip, self.remote_ip:
            for login in 'somebody', 'root':
                for timeout in self.timeout, None:
                    for suppress_logs in False, True:
                        with self.subTest(ip=ip, login=login, supress_logs=suppress_logs):
                            ### Setup ###
                            self.console.reset_mock()
                            responder_mock.reset_mock()
                            self.connection._logger.raw_emit.reset_mock()

                            self.connection._ip = ip_address
                            self.connection._login = login

                            cmd = self.cmd if login == 'root' else f'sudo {self.cmd}'

                            def se(*args, **kwargs):
                                raise socket.timeout

                            self.console.run.side_effect = se
                            self.console.local.side_effect = se

                            ### Run ###

                            with self.assertRaises(LoginFailed) as context:
                                self.connection.run_command(self.cmd, timeout, suppress_logs)

                            ### Assertions ###

                            self.assertEqual(ip_address, context.exception.ip)
                            self.assertEqual(login, context.exception.login)

                            if ip_address == self.localhost_ip:
                                self.console.local.assert_called_once_with(
                                    cmd,
                                    pty=True,
                                    ide='both',
                                    watchers=[responder_mock.return_value],
                                    timeout=timeout if timeout else self.connection._exec_tm
                                )
                            elif ip_address == self.remote_ip:
                                self.console.run.assert_called_once_with(
                                    cmd,
                                    pty=True,
                                    hide='both',
                                    watchers=[responder_mock.return_value],
                                    timeout=timeout if timeout else self.connection._exec_tm
                                )
                            responder_mock.assert_called_once_with(
                                pattern=self.pattern, response=f'{self.connection._password}\n')

                            if not suppress_logs:
                                expected_calls = [call(f'{login}@{ip_address}:~$ {cmd}')]
                                self.assertEqual(
                                    expected_calls,
                                    self.connection._logger.raw_emit.call_args_list)
                            if suppress_logs:
                                self.connection._logger.raw_emit.assert_not_called()

                            self.console.__enter__.assert_called_once()
                            self.console.__exit__.assert_called_once()


class TestRunCommandIgnoreFail(TestConnection):
    """
    Unit tests for "Connection.run_command_ignore_fail" method
    """

    def setUp(self) -> None:
        """Set up test."""
        super().setUp()

        self.output = ['line1', 'line2']
        self.connection.run_command = Mock(return_value=self.output)
        self.suppress_logs = Mock()

        self.command = 'some command'
        self.timeout = Mock()

    def test_returns_output_on_successful_exec(self):
        """
        Tests that if "run_command" method
        has been executed without error,
        it's output is returned
        """
        ### Run ###

        result = self.connection.run_command_ignore_fail(
            self.command, self.timeout, self.suppress_logs)

        ### Assertions ####

        self.connection.run_command.assert_called_once_with(
            self.command, self.timeout, self.suppress_logs, None, True)
        self.assertEqual(self.output, result)

    def test_returns_exception_output_on_failure(self):
        """
        Tests that if "run_command" method
        raised CommandFailed exception on execution,
        exception output is returned
        """
        ### Setup ###

        self.connection.run_command.side_effect = CommandFailed(
            self.command, self.output, Mock(), 1)

        ### Run ###

        result = self.connection.run_command_ignore_fail(
            self.command, self.timeout, self.suppress_logs)

        ### Assertions ####

        self.connection.run_command.assert_called_once_with(
            self.command, self.timeout, self.suppress_logs, None, True)
        self.assertEqual(self.output, result)


class TestGet(TestConnection):
    """
    Unit tests for "Connection.get" method
    """

    @patch('console.connection.scp')
    def test_get(self, mock_scp):
        """Test method successful execution."""
        ### Setup ###

        console = MagicMock()
        console.__enter__.return_value = console
        self.connection._get_console = Mock(return_value=console)
        remote_path = 'far far away'
        local_path = 'nearby'

        ### Run ###

        self.connection.get(remote_path=remote_path, local_path=local_path)

        ### Assertions ###

        console.__enter__.assert_called_once()
        console.__exit__.assert_called_once()
        console.open.assert_called_once()
        mock_scp.WISPClient.assert_called_once_with(transport=console.transport)
        mock_scp.WISPClient.return_value.get.assert_called_once_with(
            remote_path=remote_path, local_path=local_path)


class TestPut(TestConnection):
    """
    Unit tests for "Connection.put" method
    """

    @patch('console.connection.scp')
    def test_put(self, mock_scp):
        """Test method successful execution."""
        ### Setup ###

        console = MagicMock()
        console.__enter__.return_value = console
        self.connection._get_console = Mock(return_value=console)
        remote_path = 'far far away'
        local_path = 'nearby'

        ### Run ###

        self.connection.put(remote_path=remote_path, local_path=local_path)

        ### Assertions ###

        console.__enter__.assert_called_once()
        console.__exit__.assert_called_once()
        console.open.assert_called_once()
        mock_scp.WISPClient.assert_called_once_with(transport=console.transport)
        mock_scp.WISPClient.return_value.put.assert_called_once_with(
            files=local_path, remote_path=remote_path)
