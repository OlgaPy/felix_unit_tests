import unittest
from unittest.mock import Mock, patch

from workers import (
    WorkerIMCEndOfTest,
    WorkerIMCFirmwareUpdatingStart,
    WorkerIMCFirmwareUpdatingEnd,
    WorkerIMCInitialTestStart,
    WorkerIMCInitialTestEnd,
    WorkerIMCStressTestStart,
    WorkerIMCStressTestEnd,
    WorkerIMCFinalTestStart,
    WorkerIMCFinalTestEnd
)
import api_provides


class TestWorkerIMCEndOfTest(unittest.TestCase):
    """Class for test WorkerIMCEndOfTest"""

    def setUp(self) -> None:
        """Setup for tests WorkerIMCEndOfTest"""
        with patch('workers._proto_worker_thread.logger'), \
                patch('workers._proto_worker_thread.controllers'):
            self.worker = WorkerIMCEndOfTest(mboard=Mock(), login=Mock(), port=Mock())

            self.worker._imc_api_provide = Mock()
            self.worker._imc_api_provide.set_transition_state.return_value = None
            self.worker._motherboard.server.serial_number = '444RRR'
            self.tested_method = self.worker._send_state.__closure__[
                0].cell_contents.__closure__[0].cell_contents

    def test_class_attrs(self) -> None:
        """
        Test the values of WorkerIMCEndOfTest's class attributes.
        """
        ### Assertions ###

        self.assertEqual(self.worker.key, 'send_IMC_end_of_test')
        self.assertEqual(self.worker.action, 'IMC End of Test')
        self.assertIs(self.worker._power_off, False)
        self.assertEqual(self.worker.roles, ['admin', 'tester', 'advanced-tester'])

    def test__send_state_exception(self):
        """Test method _send_state with unexpected fail"""
        ### Set Up ###

        self.worker._imc_api_provide.set_transition_state.side_effect = Exception

        ### Run ###

        result = self.tested_method(self.worker)

        ### Assertions ###

        self.worker._imc_api_provide.assert_not_called()
        self.worker.logger.success.assert_not_called()
        self.worker.logger.warning.assert_not_called()
        self.worker.logger.failure.assert_called_once_with('Failed set IMC state.', exc_info=True)
        self.assertIs(result, False)

    def test__send_state_provide_error(self):
        """Test method _send_state with provide error"""
        ### Set Up ###

        self.worker._imc_api_provide.set_transition_state.side_effect = api_provides.ProvideError

        ### Run ###

        result = self.tested_method(self.worker)

        ### Assertions ###

        self.worker._imc_api_provide.assert_not_called()
        self.worker.logger.success.assert_not_called()
        self.worker.logger.warning.assert_not_called()
        self.worker.logger.failure.assert_called_once_with(
            f'Failed set IMC state: {api_provides.ProvideError.info}'
        )
        self.assertIs(result, False)

    def test__send_state_bare(self):
        """Test method _send_state with fail by server BARE_"""
        ### Set Up ###

        self.worker._motherboard.server.serial_number = 'BARE_123'

        ### Run ###

        result = self.tested_method(self.worker)

        ### Assertions ###

        self.worker._imc_api_provide.assert_not_called()
        self.worker.logger.success.assert_not_called()
        self.worker.logger.failure.assert_not_called()
        self.worker.logger.warning.assert_called_once_with(
            f'Wrong server serial number was passed - '
            f'{self.worker._motherboard.server.serial_number}'
        )
        self.assertIs(result, False)

    def test__send_state_success(self):
        """Test method _send_state with success result"""
        ### Run ###

        result = self.tested_method(self.worker)

        ### Assertions ###

        self.worker.logger.info.assert_called_once_with(
            f'Sending new state for IMC - {self.worker.action}')
        self.worker._imc_api_provide.set_transition_state.assert_called_once_with(
            product_sn=self.worker._motherboard.server.serial_number,
            login=self.worker._login.login
        )
        self.worker.logger.success.assert_called_once_with(
            f'IMC state {self.worker.action} set successful')
        self.worker.logger.failure.assert_not_called()
        self.worker.logger.warning.assert_not_called()
        self.assertIs(result, True)


class TestWorkerIMCFirmwareUpdatingStart(unittest.TestCase):
    """Class for test WorkerIMCFirmwareUpdatingStart"""

    def test_class_attrs(self) -> None:
        """
        Test the values of WorkerIMCFirmwareUpdatingStart's class attributes.
        """
        worker = WorkerIMCFirmwareUpdatingStart

        ### Assertions ###
        self.assertEqual(worker.key, 'send_imc_firmware_updating_start')
        self.assertEqual(worker.action, 'IMC Firmware Updating Start')
        self.assertEqual(worker.operation_type_id, 2)
        self.assertEqual(worker.operation_stage_id, 1)


class TestWorkerIMCFirmwareUpdatingEnd(unittest.TestCase):
    """Class for test WorkerIMCFirmwareUpdatingEnd"""

    def test_class_attrs(self) -> None:
        """
        Test the values of WorkerIMCFirmwareUpdatingEnd's class attributes.
        """
        worker = WorkerIMCFirmwareUpdatingEnd

        ### Assertions ###
        self.assertEqual(worker.key, 'send_imc_firmware_updating_end')
        self.assertEqual(worker.action, 'IMC Firmware Updating End')
        self.assertEqual(worker.operation_type_id, 2)
        self.assertEqual(worker.operation_stage_id, 2)
        self.assertIs(worker.extra_params.get('passed'), True)


class TestWorkerIMCStressTestStart(unittest.TestCase):
    """Class for test WorkerIMCStressTestStart"""

    def test_class_attrs(self) -> None:
        """
        Test the values of WorkerIMCStressTestStart's class attributes.
        """
        worker = WorkerIMCStressTestStart

        ### Assertions ###
        self.assertEqual(worker.key, 'send_imc_stress_test_start')
        self.assertEqual(worker.action, 'IMC Stress Testing Start')
        self.assertEqual(worker.operation_type_id, 5)
        self.assertEqual(worker.operation_stage_id, 1)
        self.assertEqual(worker.test_type_id, 3)


class TestWorkerIMCStressTestEnd(unittest.TestCase):
    """Class for test WorkerIMCStressTestEnd"""

    def test_class_attrs(self) -> None:
        """
        Test the values of WorkerIMCStressTestEnd's class attributes.
        """
        worker = WorkerIMCStressTestEnd

        ### Assertions ###
        self.assertEqual(worker.key, 'send_imc_stress_test_end')
        self.assertEqual(worker.action, 'IMC Stress Testing End')
        self.assertEqual(worker.operation_type_id, 5)
        self.assertEqual(worker.operation_stage_id, 2)
        self.assertIs(worker.extra_params.get('passed'), True)


class TestWorkerIMCInitialTestStart(unittest.TestCase):
    """Class for test WorkerIMCInitialTestStart"""

    def test_class_attrs(self) -> None:
        """
        Test the values of WorkerIMCInitialTestStart's class attributes.
        """
        worker = WorkerIMCInitialTestStart

        ### Assertions ###
        self.assertEqual(worker.key, 'send_imc_initial_test_start')
        self.assertEqual(worker.action, 'IMC Initial Testing Start')
        self.assertEqual(worker.operation_type_id, 5)
        self.assertEqual(worker.operation_stage_id, 1)
        self.assertEqual(worker.test_type_id, 2)


class TestWorkerIMCInitialTestEnd(unittest.TestCase):
    """Class for test WorkerIMCInitialTestEnd"""

    def test_class_attrs(self) -> None:
        """
        Test the values of WorkerIMCInitialTestEnd's class attributes.
        """
        worker = WorkerIMCInitialTestEnd

        ### Assertions ###
        self.assertEqual(worker.key, 'send_imc_initial_test_end')
        self.assertEqual(worker.action, 'IMC Initial Testing End')
        self.assertEqual(worker.operation_type_id, 5)
        self.assertEqual(worker.operation_stage_id, 2)
        self.assertIs(worker.extra_params.get('passed'), True)


class TestWorkerIMCFinalTestStart(unittest.TestCase):
    """Class for test WorkerIMCFinalTestStart"""

    def test_class_attrs(self) -> None:
        """
        Test the values of WorkerIMCFinalTestStart's class attributes.
        """
        worker = WorkerIMCFinalTestStart

        ### Assertions ###
        self.assertEqual(worker.key, 'send_imc_final_test_start')
        self.assertEqual(worker.action, 'IMC Final Testing Start')
        self.assertEqual(worker.operation_type_id, 5)
        self.assertEqual(worker.operation_stage_id, 1)
        self.assertEqual(worker.test_type_id, 1)


class TestWorkerIMCFinalTestEnd(unittest.TestCase):
    """Class for test WorkerIMCFinalTestEnd"""

    def test_class_attrs(self) -> None:
        """
        Test the values of WorkerIMCFinalTestEnd's class attributes.
        """
        worker = WorkerIMCFinalTestEnd

        ### Assertions ###
        self.assertEqual(worker.key, 'send_imc_final_test_end')
        self.assertEqual(worker.action, 'IMC Final Testing End')
        self.assertEqual(worker.operation_type_id, 5)
        self.assertEqual(worker.operation_stage_id, 2)
        self.assertIs(worker.extra_params.get('passed'), True)
