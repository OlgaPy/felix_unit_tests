from unittest.mock import patch, Mock

import database
import enums
from tests.test_web.namespaces.api_test_case import APITestCase

from peewee import fn


class TestUserEndpoint(APITestCase):
    """Base class for '/login' endpoint."""

    def setUp(self) -> None:
        """Setting up API test case. DB initialization and test login creation."""
        super().setUp()
        self.test_login = database.Users.add(
            login='test_usr',
            first_name='test_usr_first_name',
            last_name='test_usr_last_name',
            mail='test_usr@example.com',
            role=enums.Roles.USER)

    def tearDown(self) -> None:
        """Tearing down API test case."""
        self.test_login.delete_instance()


class TestUserGet(TestUserEndpoint):
    """Test GET /login/<int:login_id> endpoint with only 'admin' role allowed to access."""

    def test_get_with_admin_role(self):
        """Test successful getting data by login with admin role."""
        ### Run ###
        resp = self.get_with_login(f'/api/login/{self.test_login.id}', enums.Roles.ADMIN)

        ### Assertions ###
        self.assertEqual(200, resp.status_code)
        self.assertEqual(self.test_login.login, resp.json['login'])
        self.assertEqual(self.test_login.first_name, resp.json['first_name'])
        self.assertEqual(self.test_login.last_name, resp.json['last_name'])
        self.assertEqual(self.test_login.mail, resp.json['mail'])
        self.assertEqual(self.test_login.role.id, resp.json['role'])
        self.assertEqual(self.test_login.company.id, resp.json['company'])

    def test_anonymous_request_not_allowed(self):
        """Test anonymous GET request to endpoint not allowed."""
        self._test_anonymous_get_not_allowed(f'/api/login/{self.test_login.id}')

    def test_get_with_not_allowed_roles(self):
        """Test not successful GET request to endpoint with not allowed role."""
        self._test_get_with_not_allowed_roles(f'/api/login/{self.test_login.id}', allowed_roles=[enums.Roles.ADMIN])

    def test_get_not_existing_login(self):
        """Test not successful getting data of not existing login."""
        ### Setup ###
        wrong_login_id = database.Users.select(fn.MAX(database.Users.id)).scalar() + 2
        expected_json_resp = {'error': 'Bad Request', 'message': f'User with ID: {wrong_login_id} does not exist!'}

        ### Run ###
        resp = self.get_with_login(f'/api/login/{wrong_login_id}', enums.Roles.ADMIN)

        ### Assertions ###
        self.assertEqual(400, resp.status_code)
        self.assertEqual(expected_json_resp, resp.json)


class TestUserPut(TestUserEndpoint):
    """Test PUT /login/<int:login_id> endpoint with only 'admin' role allowed to access."""

    def setUp(self) -> None:
        """Set up API test case."""
        super().setUp()
        self.another_role = database.Roles.get_by_id((self.test_login.id + 1) % 8)
        self.another_company = database.Companies.add(name='another_company')

    def test_login_successfully_updated(self):
        """Test login was successfully updated."""
        ### Setup ###
        variants = (
            (self.another_role.id, self.test_login.company.id),
            (self.test_login.role.id, self.another_company.id)
        )

        ### Run ###
        for new_role, new_company in variants:
            with self.subTest(new_role=new_role, new_company=new_company):
                params = {'role': new_role, 'company': new_company}
                resp = self.put_with_login(f'/api/login/{self.test_login.id}', enums.Roles.ADMIN, json=params)
                login_in_db_after_update = database.Users.get_by_id(self.test_login.id)

                ### Assertions ###
                self.assertEqual(200, resp.status_code)
                self.assertEqual({'message': 'test_usr updated', 'success': 'OK'}, resp.json)
                self.assertEqual(new_role, login_in_db_after_update.role.id)
                self.assertEqual(new_company, login_in_db_after_update.company.id)

    def test_request_without_updating(self):
        """Test login was not updated because the information is not new."""
        ### Run ###
        params = {'role': self.test_login.role.id, 'company': self.test_login.company.id}
        resp = self.put_with_login(f'/api/login/{self.test_login.id}', enums.Roles.ADMIN, json=params)
        login_in_db_after_update = database.Users.get_by_id(self.test_login.id)

        ### Assertions ###
        self.assertEqual(200, resp.status_code)
        self.assertEqual({'success': 'OK'}, resp.json)
        self.assertEqual(self.test_login.role.id, login_in_db_after_update.role.id)
        self.assertEqual(self.test_login.company.id, login_in_db_after_update.company.id)

    def test_updating_not_existing_login(self):
        """Test not successful updating data of not existing login."""
        ### Setup ###
        wrong_login_id = database.Users.select(fn.MAX(database.Users.id)).scalar() + 2
        expected_json_resp = {'error': 'Bad Request', 'message': f'User with ID: {wrong_login_id} does not exist!'}
        params = {'role': self.test_login.role.id, 'company': self.test_login.company.id}

        ### Run ###
        resp = self.put_with_login(f'/api/login/{wrong_login_id}', enums.Roles.ADMIN, json=params)

        ### Assertions ###
        self.assertEqual(400, resp.status_code)
        self.assertEqual(expected_json_resp, resp.json)

    def test_new_role_id_not_exits_in_db(self):
        """Test login was not updated because role id not exits in DB."""
        ### Run ###
        role_id = 999  # not exists in DB
        params = {'role': role_id, 'company': self.test_login.company.id}
        resp = self.put_with_login(f'/api/login/{self.test_login.id}', enums.Roles.ADMIN, json=params)
        login_in_db_after_update = database.Users.get_by_id(self.test_login.id)

        ### Assertions ###
        self.assertEqual(400, resp.status_code)
        self.assertEqual({'error': 'Bad Request', 'message': f'Role with ID: {role_id} does not exist!'}, resp.json)
        self.assertEqual(self.test_login.role.id, login_in_db_after_update.role.id)
        self.assertEqual(self.test_login.company.id, login_in_db_after_update.company.id)

    def test_new_company_id_not_exits_in_db(self):
        """Test login was not updated because company id not exits in DB."""
        ### Run ###
        company_id = 999999  # not exists in DB
        params = {'role': self.test_login.role.id, 'company': company_id}
        resp = self.put_with_login(f'/api/login/{self.test_login.id}', enums.Roles.ADMIN, json=params)
        login_in_db_after_update = database.Users.get_by_id(self.test_login.id)

        ### Assertions ###
        self.assertEqual(400, resp.status_code)
        self.assertEqual(
            {'error': 'Bad Request', 'message': f'Company with ID: {company_id} does not exist!'},
            resp.json
        )
        self.assertEqual(self.test_login.company.id, login_in_db_after_update.company.id)
        self.assertEqual(self.test_login.role.id, login_in_db_after_update.role.id)

    def test_anonymous_put_request_not_allowed(self):
        """Test anonymous PUT request to endpoint not allowed."""
        self._test_anonymous_put_not_allowed(f'/api/login/{self.test_login.id}')

    def test_put_with_not_allowed_roles(self):
        """Test not successful PUT request to endpoint with not allowed role."""
        params = {'role': self.test_login.role.id, 'company': self.test_login.company.id}
        self._test_put_with_not_allowed_roles(
            f'/api/login/{self.test_login.id}',
            allowed_roles=[enums.Roles.ADMIN],
            json=params
        )


class TestGetUserRoles(APITestCase):
    """Test GET /login/roles endpoint with only 'admin' role allowed to access."""

    def test_get_with_admin_role(self):
        """Test successful getting roles data by admin role."""
        ### Setup ###
        expected_resp_json = {"roles": [{"id": role.id, "name": role.name} for role in database.Roles.select()]}

        ### Run ###
        resp = self.get_with_login('/api/login/roles', enums.Roles.ADMIN)

        ### Assertions ###
        self.assertEqual(200, resp.status_code)
        self.assertEqual(expected_resp_json, resp.json)

    def test_anonymous_request_not_allowed(self):
        """Test anonymous GET request to endpoint not allowed."""
        self._test_anonymous_get_not_allowed('/api/login/roles')

    def test_get_with_not_allowed_roles(self):
        """Test not successful GET request to endpoint with not allowed role."""
        self._test_get_with_not_allowed_roles('/api/login/roles', allowed_roles=[enums.Roles.ADMIN])


class TestGetUserCompanies(APITestCase):
    """Test GET /login/companies endpoint with only 'admin' role allowed to access."""

    def test_get_with_admin_role(self):
        """Test successful getting roles data by admin role."""
        ### Setup ###
        expected_resp_json = {"companies": [{"id": role.id, "name": role.name} for role in database.Companies.select()]}

        ### Run ###
        resp = self.get_with_login('/api/login/companies', enums.Roles.ADMIN)

        ### Assertions ###
        self.assertEqual(200, resp.status_code)
        self.assertEqual(expected_resp_json, resp.json)

    def test_anonymous_request_not_allowed(self):
        """Test anonymous GET request to endpoint not allowed."""
        self._test_anonymous_get_not_allowed('/api/login/companies')

    def test_get_with_not_allowed_roles(self):
        """Test not successful GET request to endpoint with not allowed role."""
        self._test_get_with_not_allowed_roles('/api/login/companies', allowed_roles=[enums.Roles.ADMIN])


class TestPostUserCompanies(TestUserEndpoint):
    """Test POST /login/companies endpoint with only 'admin' role allowed to access."""

    def test_send_post_by_admin(self):
        """Test send POST request to endpoint by admin login."""
        ### Setup ###
        new_company_name = 'Test New Company Name'

        ### Run ###
        resp = self.post_with_login('/api/login/companies', enums.Roles.ADMIN, json={'name': new_company_name})

        ### Assertions ###
        self.assertEqual(201, resp.status_code)
        self.assertEqual({'message': f'{new_company_name} Successfully Created', 'success': 'Created'}, resp.json)

        new_companies_in_db = database.Companies.select().where(database.Companies.name == new_company_name).execute()
        self.assertEqual(1, len(new_companies_in_db))

    def test_company_name_already_taken(self):
        """Test send POST request to endpoint by admin login with already taken company name."""
        ### Setup ###
        company_name = 'Test Company Name'
        another_company = database.Companies.add(company_name)

        ### Run ###
        resp = self.post_with_login('/api/login/companies', enums.Roles.ADMIN, json={'name': company_name})

        ### Assertions ###
        self.assertEqual(409, resp.status_code)
        self.assertEqual({'error': 'Conflict', 'message': f'Name {company_name} already taken'}, resp.json)
        another_company.delete_instance()

    def test_anonymous_post_request_not_allowed(self):
        """Test anonymous POST request to endpoint not allowed."""
        self._test_anonymous_post_not_allowed('/api/login/companies', json={'name': 'Test Company Name'})

    def test_post_with_not_allowed_roles(self):
        """Test not successful POST request to endpoint with not allowed role."""
        self._test_post_with_not_allowed_roles(
            '/api/login/companies',
            json={'name': 'Test Company Name'},
            allowed_roles=[enums.Roles.ADMIN]
        )


class TestPutUserCompany(TestUserEndpoint):
    """Test PUT /login/companies endpoint with only 'admin' role allowed for access."""

    def setUp(self) -> None:
        """Setting up API test case. DB initialization and test company creation."""
        super().setUp()
        self.company = database.Companies.get_by_id(self.test_login.company.id)
        self.original_company_name = self.company.name
        self.new_company_name = 'Company Name v2'
        self.request_data = {'id': self.test_login.company.id, 'name': self.new_company_name}

    def tearDown(self) -> None:
        """Tearing down API test case."""
        super().tearDown()
        self.company.name = self.original_company_name
        self.company.save()

    def test_send_put_by_admin_when_name_changing_is_happened(self):
        """Test send PUT request to endpoint by admin login when name changing is happened."""
        ### Run ###
        resp = self.put_with_login('/api/login/companies', enums.Roles.ADMIN, json=self.request_data)

        ### Assertions ###
        self.assertEqual(200, resp.status_code)
        self.assertEqual(
            {'message': f'{self.original_company_name} updated to {self.new_company_name}', 'success': 'OK'},
            resp.json
        )
        self.assertEqual(database.Companies.get_by_id(self.test_login.company.id).name, self.new_company_name)

    def test_send_put_by_admin_when_no_changes_are_happened(self):
        """Test send PUT request to endpoint by admin login when no changes are happened."""
        ### Setup ###
        self.request_data['name'] = self.original_company_name

        ### Run ###
        resp = self.put_with_login('/api/login/companies', enums.Roles.ADMIN, json=self.request_data)

        ### Assertions ###
        self.assertEqual(200, resp.status_code)
        self.assertEqual(
            {'message': f'{self.original_company_name} updated to {self.original_company_name}', 'success': 'OK'},
            resp.json
        )
        self.assertEqual(database.Companies.get_by_id(self.test_login.company.id).name, self.original_company_name)

    def test_sending_company_id_that_not_exists_in_db(self):
        """Test send PUT request to endpoint with id of not existing company."""
        ### Setup ###
        not_existing_company_id = database.Companies.select().count() + 2
        self.request_data['id'] = not_existing_company_id

        ### Run ###
        resp = self.put_with_login('/api/login/companies', enums.Roles.ADMIN, json=self.request_data)

        ### Assertions ###
        self.assertEqual(400, resp.status_code)
        self.assertEqual(
            {'error': 'Bad Request', 'message': f'Company with ID: {not_existing_company_id} does not exist!'},
            resp.json
        )

    def test_company_name_already_taken(self):
        """Test send PUT request to endpoint by admin login with already taken company name."""
        ### Setup ###
        another_company = database.Companies.add(self.new_company_name)

        ### Run ###
        resp = self.put_with_login('/api/login/companies', enums.Roles.ADMIN, json=self.request_data)

        ### Assertions ###
        self.assertEqual(409, resp.status_code)
        self.assertEqual({'error': 'Conflict', 'message': f'Name {self.new_company_name} already taken'}, resp.json)
        another_company.delete_instance()

    def test_anonymous_put_request_not_allowed(self):
        """Test anonymous PUT request to endpoint not allowed."""
        self._test_anonymous_put_not_allowed('/api/login/companies', json=self.request_data)

    def test_put_with_not_allowed_roles(self):
        """Test not successful PUT request to endpoint with not allowed role."""
        self._test_put_with_not_allowed_roles(f'/api/login/{self.test_login.id}',
                                              allowed_roles=[enums.Roles.ADMIN],
                                              json=self.request_data
                                              )


class TestGetUserActions(TestUserEndpoint):
    """Test GET request for /login/actions endpoint."""

    def setUp(self) -> None:
        """Setting up API test case. DB initialization and test action creation."""
        super().setUp()
        self.workers = {
            'worker_a': Mock(key='action_a', action='Action A', roles=[enums.Roles.ADMIN, enums.Roles.ADVANCED_TESTER]),
            'worker_b': Mock(key='action_b', action='Action B', roles=[enums.Roles.ADVANCED_TESTER]),
            'worker_c': Mock(key='action_c', action='Action C', roles=[enums.Roles.ADMIN])
        }
        self.actions = {worker.key: database.Actions.add(worker.action) for worker in self.workers.values()}

    def tearDown(self) -> None:
        """Tearing down API test case."""
        [action.delete_instance() for action in self.actions.values()]

    @patch('web.namespaces.logins.threads.ThreadHolder.get_jobs_pool')
    def test_getting_actions_if_role_is_allowed(self, get_jobs_pool_mock):
        """Test GET payload with actions info if login role is allowed."""
        ### Setup ###
        get_jobs_pool_mock.return_value = Mock(
            keys=self.workers.keys(),
            action=Mock(side_effect=lambda key: self.workers.get(key).action if key in self.workers else None),
            roles=Mock(side_effect=lambda key: self.workers.get(key).roles if key in self.workers else None),
            description=Mock(
                side_effect=lambda key: f"description_{self.workers.get(key).action}" if key in self.workers else None
            ),
            category=Mock(
                side_effect=lambda key: f"category_{self.workers.get(key).action}" if key in self.workers else None
            )
        )
        expected_payload = {
            enums.Roles.ADMIN.name: {'actions': [
                {
                    'id': self.actions['action_a'].id,
                    'name': self.actions['action_a'].name,
                    'key': 'worker_a',
                    'description': f"description_{self.workers['worker_a'].action}",
                    'category': f"category_{self.workers['worker_a'].action}"
                },
                {
                    'id': self.actions['action_c'].id,
                    'name': self.actions['action_c'].name,
                    'key': 'worker_c',
                    'description': f"description_{self.workers['worker_c'].action}",
                    'category': f"category_{self.workers['worker_c'].action}"
                }
            ]},
            enums.Roles.ADVANCED_TESTER.name: {'actions': [
                {
                    'id': self.actions['action_a'].id,
                    'name': self.actions['action_a'].name,
                    'key': 'worker_a',
                    'description': f"description_{self.workers['worker_a'].action}",
                    'category': f"category_{self.workers['worker_a'].action}"
                },
                {
                    'id': self.actions['action_b'].id,
                    'name': self.actions['action_b'].name,
                    'key': 'worker_b',
                    'description': f"description_{self.workers['worker_b'].action}",
                    'category': f"category_{self.workers['worker_b'].action}"
                }
            ]}
        }

        ### Run ###
        for role in [enums.Roles.ADMIN, enums.Roles.ADVANCED_TESTER]:
            resp = self.get_with_login('/api/login/actions', role)

            ### Assertions ###
            self.assertEqual(200, resp.status_code)
            self.assertEqual(expected_payload[role.name], resp.json)

    def test_getting_empty_resp_if_role_is_not_allowed(self):
        """Test GET empty response if login role is not allowed."""
        ### Setup ###
        allowed_roles = [enums.Roles.ADMIN, enums.Roles.ADVANCED_TESTER]
        not_allowed_roles = [role for role in enums.Roles if role not in allowed_roles]

        ### Run ###
        for role in not_allowed_roles:
            resp = self.get_with_login('/api/login/actions', role)

            ### Assertions ###
            self.assertEqual(200, resp.status_code)
            self.assertEqual({'actions': []}, resp.json)
