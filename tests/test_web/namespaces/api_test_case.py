import typing
import unittest
from unittest.mock import patch

import werkzeug
from flask import Flask
from web import create_app

import enums
import database
from database.db_manager import DBManager


class LoginHandler:
    """Context manager for login/logout requests to API."""

    def __init__(self, api_client, login_role: enums.Roles):
        self.api_client = api_client
        self.login = self._create_login(login_role)
        self.token = ''
        self.refresh_token = ''

    @staticmethod
    def _create_login(login_role: enums.Roles) -> database.Users:
        """Create login in test DB with necessary role."""
        return database.Users.add(
            login=login_role.value,
            first_name=f'{login_role.value}_first_name',
            last_name=f'{login_role.value}_last_name',
            mail=f'{login_role.value}@example.com',
            role=login_role
        )

    def __enter__(self):
        with patch('web.namespaces.auth.ldap_connector') as ldap_connector_mock:
            ldap_connector_mock.check_login.return_value = True
            ldap_connector_mock.get_login.return_value = self.login
            resp = self.api_client.post('/api/auth/login', json={}, follow_redirects=True)
            self.token = resp.json.get('token')
            self.refresh_token = resp.json.get('refresh_token')
            return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        auth_headers = {'Authorization': f'Bearer {self.token}'}
        self.api_client.post('/api/auth/logout', headers=auth_headers, follow_redirects=True)


class APITestCase(unittest.TestCase):
    """
    Test case for API tests
    """

    app: Flask

    @classmethod
    def setUpClass(cls) -> None:
        """
        Sets up API Test Case environment
        """
        DBManager.initialize_test_data_base()
        DBManager.create_tables()
        DBManager.check_defaults()
        cls.app = create_app()
        cls.app.testing = True
        cls.api_client = cls.app.testprovide(use_cookies=False)
        cls.current_login = None

    def tearDown(self) -> None:
        """Restore initial state of DB."""
        self.restore_initial_db()

    @staticmethod
    def restore_initial_db() -> None:
        """Restore initial state of DB."""
        db_models = DBManager.get_models()
        for db_model in sorted(db_models, key=lambda x: x.migration_priority, reverse=True):
            db_model.delete().execute()
            if hasattr(db_model, 'add') and hasattr(db_model.add, 'cache_clear'):
                db_model.add.cache_clear()
        DBManager.check_defaults()

    def _request_with_login(
            self,
            url: str,
            login_role: enums.Roles,
            request_method_name: str,
            json: typing.Optional[dict],
            follow_redirects=True) -> werkzeug.test.TestResponse:
        with LoginHandler(self.api_client, login_role) as handler:
            self.current_login = handler.login
            request_method = getattr(self.api_client, request_method_name)
            headers = {'Authorization': f'Bearer {handler.token}'}
            resp = request_method(
                url,
                json=json,
                headers=headers,
                follow_redirects=follow_redirects)
        return resp

    def get_with_login(
            self,
            url: str,
            login_role: enums.Roles,
            json: typing.Optional[dict] = None,
            follow_redirects: bool = True) -> werkzeug.test.TestResponse:
        """Login and send GET request to API."""
        return self._request_with_login(
            url=url,
            login_role=login_role,
            request_method_name='get',
            json=json,
            follow_redirects=follow_redirects
        )

    def post_with_login(
            self,
            url: str,
            login_role: enums.Roles,
            json: typing.Optional[dict] = None,
            follow_redirects: bool = True) -> werkzeug.test.TestResponse:
        """Login and send POST request to API."""
        return self._request_with_login(
            url=url,
            login_role=login_role,
            request_method_name='post',
            json=json,
            follow_redirects=follow_redirects
        )

    def put_with_login(
            self,
            url: str,
            login_role: enums.Roles,
            json: typing.Optional[dict] = None,
            follow_redirects: bool = True) -> werkzeug.test.TestResponse:
        """Login and send PUT request to API."""
        return self._request_with_login(
            url=url,
            login_role=login_role,
            request_method_name='put',
            json=json,
            follow_redirects=follow_redirects
        )

    def delete_with_login(
            self,
            url: str,
            login_role: enums.Roles,
            json: typing.Optional[dict] = None,
            follow_redirects: bool = True) -> werkzeug.test.TestResponse:
        """Login and send DELETE request to API."""
        return self._request_with_login(
            url=url,
            login_role=login_role,
            request_method_name='delete',
            json=json,
            follow_redirects=follow_redirects
        )

    def _test_anonymous_method_not_allowed(
            self,
            url: str,
            method: str,
            json: typing.Optional[typing.Dict] = None):
        """Test anonymous METHOD request to endpoint not allowed."""
        ### Setup ###
        expected_resp_json = {
            'error': 'Unauthorized',
            'message': f'Unauthorized access attempt at {url}'
        }

        ### Run ###
        if method.lower() == 'get':
            resp = self.api_client.get(url, follow_redirects=True)
        elif method.lower() == 'post':
            resp = self.api_client.post(url, json=json, follow_redirects=True)
        elif method.lower() == 'put':
            resp = self.api_client.put(url, json=json, follow_redirects=True)
        elif method.lower() == 'delete':
            resp = self.api_client.delete(url, follow_redirects=True)
        else:
            raise Exception('method not specified.')

        ### Assertions ###
        self.assertEqual(401, resp.status_code)
        self.assertTrue(expected_resp_json, resp.json)

    def _test_anonymous_get_not_allowed(self, url: str):
        """Test anonymous GET request to endpoint not allowed."""
        self._test_anonymous_method_not_allowed(url, 'get')

    def _test_anonymous_post_not_allowed(self, url: str, json: typing.Optional[typing.Dict] = None):
        """Test anonymous POST request to endpoint not allowed."""
        self._test_anonymous_method_not_allowed(url, 'post', json=json)

    def _test_anonymous_put_not_allowed(self, url: str, json: typing.Optional[typing.Dict] = None):
        """Test anonymous PUT request to endpoint not allowed."""
        self._test_anonymous_method_not_allowed(url, 'put', json=json)

    def _test_anonymous_delete_not_allowed(self, url: str):
        """Test anonymous DELETE request to endpoint not allowed."""
        self._test_anonymous_method_not_allowed(url, 'delete')

    def _test_method_with_not_allowed_roles(
            self,
            url: str,
            method: str,
            json: typing.Optional[typing.Dict] = None,
            allowed_roles=typing.Optional[typing.List[enums.Roles]],
            prohibited_roles=typing.Optional[typing.List[enums.Roles]]):
        """Test not successful METHOD request to endpoint with not allowed role."""
        ### Setup ###
        expected_resp_json = {
            'error': 'Forbidden',
            'message': f"login doesn't have permission to access {url}!"
        }

        ### Run ###
        if allowed_roles:
            prohibited_roles = [element for element in enums.Roles if element not in allowed_roles]
        for role in prohibited_roles:
            with self.subTest(role=role):
                if method.lower() == 'get':
                    resp = self.get_with_login(url, role)
                elif method.lower() == 'post':
                    resp = self.post_with_login(url, role, json=json)
                elif method.lower() == 'put':
                    resp = self.put_with_login(url, role, json=json)
                elif method.lower() == 'delete':
                    resp = self.delete_with_login(url, role, json=json)
                else:
                    raise Exception('method not specified.')

                ### Assertions ###
                self.assertEqual(403, resp.status_code)
                self.assertTrue(expected_resp_json, resp.json)

    def _test_get_with_not_allowed_roles(
            self,
            url: str,
            allowed_roles=typing.Optional[typing.List[enums.Roles]],
            prohibited_roles=typing.Optional[typing.List[enums.Roles]]):
        """Test not successful GET request to endpoint with not allowed role."""
        self._test_method_with_not_allowed_roles(url, 'get', {}, allowed_roles, prohibited_roles)

    def _test_post_with_not_allowed_roles(
            self,
            url: str,
            json: typing.Optional[typing.Dict] = None,
            allowed_roles=typing.Optional[typing.List[enums.Roles]],
            prohibited_roles=typing.Optional[typing.List[enums.Roles]]):
        """Test not successful POST request to endpoint with not allowed role."""
        self._test_method_with_not_allowed_roles(
            url=url,
            method='post',
            json=json,
            allowed_roles=allowed_roles,
            prohibited_roles=prohibited_roles)

    def _test_put_with_not_allowed_roles(
            self,
            url: str,
            json: typing.Optional[typing.Dict] = None,
            allowed_roles=typing.Optional[typing.List[enums.Roles]],
            prohibited_roles=typing.Optional[typing.List[enums.Roles]]):
        """Test not successful PUT request to endpoint with not allowed role."""
        self._test_method_with_not_allowed_roles(
            url=url,
            method='put',
            json=json,
            allowed_roles=allowed_roles,
            prohibited_roles=prohibited_roles)

    def _test_delete_with_not_allowed_roles(
            self,
            url: str,
            json: typing.Optional[typing.Dict] = None,
            allowed_roles=typing.Optional[typing.List[enums.Roles]],
            prohibited_roles=typing.Optional[typing.List[enums.Roles]]):
        """Test not successful DELETE request to endpoint with not allowed role."""
        self._test_method_with_not_allowed_roles(
            url=url,
            method='delete',
            json=json,
            allowed_roles=allowed_roles,
            prohibited_roles=prohibited_roles)
