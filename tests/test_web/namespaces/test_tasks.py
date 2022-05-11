from unittest.mock import patch, Mock

from celery import states

import enums
from tests.test_web.namespaces.api_test_case import APITestCase


class TestTasksEndpoint(APITestCase):
    """Base class for testing '/api/tasks' endpoint."""

    def setUp(self) -> None:
        """Setting up API test case. DB initialization."""
        super().setUp()


@patch('web.common.url_for')
@patch('web.namespaces.tasks.AsyncResult')
@patch('web.namespaces.tasks.redis_state')
class TestTasksGet(TestTasksEndpoint):
    """Test GET /api/tasks/<task_id> endpoint."""

    def setUp(self) -> None:
        """Set up test attributes."""
        super().setUp()
        self.task_id = '123'

    def test_task_not_complete_without_result(
            self,
            redis_state_mock,
            async_result_mock,
            url_for_mock):
        """
        Test that task exists and is not complete without result.
        """
        ### Setup ###
        url_for_mock.return_value = '/Some/Location'
        for task_state in [states.PENDING, states.RECEIVED, states.STARTED, states.RETRY]:
            [mock.reset_mock() for mock in (async_result_mock, url_for_mock)]
            test_task = Mock(state=task_state)
            test_task.name = 'test_name'
            redis_state_mock.get.return_value = test_task
            async_result_mock.return_value = test_task
            expected_json_resp = {'state': task_state, 'success': 'OK', 'task_id': self.task_id}

            ### Run ###
            resp = self.get_with_login(f'/api/tasks/{self.task_id}', enums.Roles.USER)

            ### Assertions ###
            self.assertEqual(200, resp.status_code)
            self.assertEqual(expected_json_resp, resp.json)
            async_result_mock.assert_called_once_with(self.task_id)
            url_for_mock.assert_called_once_with('Tasks_task', task_id=self.task_id)
            self.assertIn(url_for_mock.return_value, resp.headers['Location'])

    def test_task_not_complete_with_progress_result(
            self,
            redis_state_mock,
            async_result_mock,
            url_for_mock):
        """
        Test that task exists and is not complete with 'PROGRESS' result.
        """
        ### Setup ###
        url_for_mock.return_value = '/Some/Location'
        test_task = Mock(state='PROGRESS')
        test_task.name = 'test_name'
        test_task.result.get.return_value = 'test progress value'
        redis_state_mock.get.return_value = test_task
        async_result_mock.return_value = test_task
        expected_json_resp = {'state': 'PROGRESS', 'success': 'OK', 'task_id': self.task_id}

        ### Run ###
        resp = self.get_with_login(f'/api/tasks/{self.task_id}', enums.Roles.USER)

        ### Assertions ###
        self.assertEqual(200, resp.status_code)
        self.assertEqual(expected_json_resp, resp.json)
        async_result_mock.assert_called_once_with(self.task_id)
        url_for_mock.assert_called_once_with('Tasks_task', task_id=self.task_id)
        self.assertIn(url_for_mock.return_value, resp.headers['Location'])
        self.assertIn(test_task.result.get.return_value, resp.headers['Task-Progress'])

    def test_task_completed_with_success_result(
            self,
            redis_state_mock,
            async_result_mock,
            url_for_mock):
        """
        Test that task exists and completed with 'SUCCESS' result.
        """
        ### Setup ###
        url_for_mock.return_value = '/Some/Location'
        test_task = Mock(state=states.SUCCESS)
        test_task.name = 'test_name'
        redis_state_mock.get.return_value = test_task
        async_result_mock.return_value = test_task
        for task_result_status_code in (200, 201):
            with self.subTest(task_result_status_code=task_result_status_code):
                [mock.reset_mock() for mock in (async_result_mock, test_task)]
                test_task.get.return_value = {
                    'status_code': task_result_status_code,
                    'success': 'OK'}

                ### Run ###
                resp = self.get_with_login(f'/api/tasks/{self.task_id}', enums.Roles.USER)

                ### Assertions ###
                self.assertEqual(task_result_status_code, resp.status_code)
                self.assertEqual(test_task.get.return_value, resp.json)
                async_result_mock.assert_called_once_with(self.task_id)
                test_task.forget.assert_called_once()

    def test_task_completed_with_not_success_result(
            self,
            redis_state_mock,
            async_result_mock,
            url_for_mock=None):
        """
        Test that task exists and completed with NOT 'SUCCESS' result.
        """
        ### Setup ###
        if url_for_mock:
            url_for_mock.return_value = '/Some/Location'
        test_task = Mock(state='SOME_FINISHED_STATE')
        test_task.name = 'test_name'
        test_task.get.return_value = 'Task Test Result'
        redis_state_mock.get.return_value = test_task
        async_result_mock.return_value = test_task
        expected_json_resp = {
            'error': 'Internal Server Error',
            'message': f"Failed to complete Task: {test_task.name} "
                       f"Error: {test_task.get.return_value}"
        }

        ### Run ###
        resp = self.get_with_login(f'/api/tasks/{self.task_id}', enums.Roles.USER)

        ### Assertions ###
        self.assertEqual(500, resp.status_code)
        self.assertEqual(expected_json_resp, resp.json)
        async_result_mock.assert_called_once_with(self.task_id)
        test_task.forget.assert_called_once()

    def test_task_not_found_in_redis(self, redis_state_mock, async_result_mock, url_for_mock=None):
        """
        Test when task not found in Redis.
        """
        if url_for_mock:
            url_for_mock.return_value = '/Some/Location'
        ### Setup ###
        test_task = Mock()
        redis_state_mock.get.return_value = None
        async_result_mock.return_value = test_task
        expected_json_resp = {
            'error': 'Not Found',
            'message': f'Unable to find task: {self.task_id}'}
        ### Run ###
        resp = self.get_with_login(f'/api/tasks/{self.task_id}', enums.Roles.USER)

        ### Assertions ###
        self.assertEqual(404, resp.status_code)
        self.assertEqual(expected_json_resp, resp.json)
        async_result_mock.assert_called_once_with(self.task_id)
