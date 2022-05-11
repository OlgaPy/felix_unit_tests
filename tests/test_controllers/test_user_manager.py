"""
Unit tests for "controllers.login_manager.UserManager" class
"""

import unittest
from unittest.mock import Mock, patch, call, PropertyMock

from controllers import UserManager, ControllerFelix


class TestUserManager(unittest.TestCase):
    """
    Base class for "UserManager" tests
    """

    def setUp(self) -> None:
        """Set up test."""
        with patch('controllers.controller_felix.logger'), \
                patch(
                    'controllers.controller_felix.ControllerFelix.motherboard_serial_number',
                    PropertyMock()), \
                patch('controllers.controller_felix.ControllerCRK'), \
                patch('controllers.controller_felix.ControllerHost'), \
                patch('controllers.controller_felix.ControllerRedfish'):
            self.manager = UserManager(motherboard=Mock(), printer=Mock())


class TestUserManagerClass(TestUserManager):
    """
    Unit tests for "UserManager" class
    """

    def test_subclass_of_controller_felix(self):
        """
        Tests that "UserManager" is a subclass
        of "ControllerFelix"
        """
        ### Assertions ###

        self.assertIs(UserManager.__base__, ControllerFelix)


class TestGetUsers(TestUserManager):
    """
    Unit tests for "UserManager._get_logins" method
    """

    def test_method(self):
        """Test method successful execution."""
        ### Setup ###

        test_logins = [Mock(), Mock()]
        self.manager.redfish.login_accounts_get.return_value = test_logins

        ### Run ###

        logins = self.manager._get_logins()

        ### Assertions ###

        self.manager.redfish.login_accounts_get.assert_called_once()
        self.assertEqual(test_logins, logins)
        self.manager.logger.info.assert_has_calls([
            call('Getting CRK login accounts'),
            call(f'Detected {len(test_logins)} login(s)'),
            call(f'1. {str(test_logins[0])}'),
            call(f'2. {str(test_logins[1])}'),
        ])


class TestCreateOrUpdateUser(TestUserManager):
    """
    Unit tests for "UserManager.create_or_update_login" method
    """

    def setUp(self) -> None:
        """Set up test."""
        super().setUp()
        self.login = 'test_usr'
        self.password = 'test_pass'
        self.role = 'test_role'
        self.suitable_login = Mock(login=self.login)
        self.not_suitable_login = Mock(login='some login')

    def test_login_entry_is_not_none_and_updating_without_error(self):
        """Test when login_entry is not None; updating account was successful."""
        ### Setup ###

        self.manager._get_logins = Mock(return_value=[self.not_suitable_login, self.suitable_login])

        ### Run ###

        self.manager.create_or_update_login(self.login, self.password, self.role)

        ### Assertions ###

        self.manager.redfish.login_account_create.assert_not_called()
        self.manager.redfish.login_account_update.assert_called_once_with(
            login=self.suitable_login, user=self.login, password=self.password, role=self.role)
        self.manager.logger.info.assert_called_once_with(f'User {self.login} present in system')
        self.manager.logger.success.assert_called_once_with(
            f'User {self.login} updated to role {self.role}')

    def test_login_entry_is_not_none_and_updating_with_error(self):
        """Test when login_entry is not None; updating account finished with exception."""
        ### Setup ###

        self.manager._get_logins = Mock(return_value=[self.not_suitable_login, self.suitable_login])
        self.manager.redfish.login_account_update.side_effect = ConnectionError

        ### Run ###

        with self.assertRaises(ConnectionError):
            self.manager.create_or_update_login(self.login, self.password, self.role)

        ### Assertions ###

        self.manager.redfish.login_account_create.assert_not_called()
        self.manager.redfish.login_account_update.assert_called_once_with(
            login=self.suitable_login, user=self.login, password=self.password, role=self.role)
        self.manager.logger.info.assert_called_once_with(f'User {self.login} present in system')
        self.manager.logger.failure.assert_called_once_with(
            f'Failed to update User {self.login} to role {self.role}!')

    def test_login_entry_is_none_and_creating_without_error(self):
        """Test when login_entry is not None; creating account was successful."""
        ### Setup ###

        self.manager._get_logins = Mock(return_value=[self.not_suitable_login])

        ### Run ###

        self.manager.create_or_update_login(self.login, self.password, self.role)

        ### Assertions ###

        self.manager.redfish.login_account_update.assert_not_called()
        self.manager.redfish.login_account_create.assert_called_once_with(
            login=self.login, password=self.password, role=self.role)
        self.manager.logger.warning.assert_called_once_with(
            f'User {self.login} missing from system')
        self.manager.logger.success.assert_called_once_with(
            f'User {self.login} with role {self.role} created!')

    def test_login_entry_is_none_and_creating_with_error(self):
        """Test when login_entry is not None; creating account got exception."""
        ### Setup ###

        self.manager._get_logins = Mock(return_value=[self.not_suitable_login])
        self.manager.redfish.login_account_create.side_effect = ConnectionError

        ### Run ###

        with self.assertRaises(ConnectionError):
            self.manager.create_or_update_login(self.login, self.password, self.role)

        ### Assertions ###

        self.manager.redfish.login_account_create.assert_called_once_with(
            login=self.login, password=self.password, role=self.role)
        self.manager.redfish.login_account_update.assert_not_called()
        self.manager.logger.warning.assert_called_once_with(
            f'User {self.login} missing from system')
        self.manager.logger.failure.assert_called_once_with(
            f'Failed to create User {self.login} with role {self.role}!')


class TestVerifyUser(TestUserManager):
    """
    Unit tests for "UserManager.create_or_update_login" method
    """

    def setUp(self) -> None:
        """Set up test."""
        super().setUp()
        self.login = 'test_usr'
        self.role = 'test_role'
        self.suitable_login = Mock(login=self.login, role=self.role)
        self.not_suitable_login1 = Mock(login=self.login, role='some role')
        self.not_suitable_login2 = Mock(login='some login', role=self.role)

    def test_success(self):
        """Test successful verification."""
        ### Setup ###

        self.manager._get_logins = Mock(
            return_value=[self.not_suitable_login1, self.suitable_login])

        ### Run ###

        result = self.manager.verify_login(self.login, self.role)

        ### Assertions ###

        self.manager._get_logins.assert_called_once()
        self.assertEqual(True, result),
        self.manager.logger.info.assert_called_once_with(
            f'Verifying Account existence {self.login} with role {self.role}')
        self.manager.logger.success.assert_called_once_with(
            f'Detected User {self.login} with role {self.role}')

    def test_not_success(self):
        """Test not successful verification."""
        ### Setup ###

        self.manager._get_logins = Mock(
            return_value=[self.not_suitable_login1, self.not_suitable_login2])

        ### Run ###

        result = self.manager.verify_login(self.login, self.role)

        ### Assertions ###

        self.manager._get_logins.assert_called_once()
        self.assertEqual(False, result),
        self.manager.logger.info.assert_called_once_with(
            f'Verifying Account existence {self.login} with role {self.role}')
        self.manager.logger.failure.assert_called_once_with(
            f'Unable to detect User {self.login} with role {self.role}')
