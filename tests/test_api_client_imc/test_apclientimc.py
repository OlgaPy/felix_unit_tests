import unittest
from unittest.mock import Mock, patch
from api_clients.api_client_imc import APIClientIMC, FelixData
import apiclient


class TestAPIClientIMC(unittest.TestCase):
    """Class for test APIClientIMC"""

    def setUp(self) -> None:
        """Setup for tests APIClientIMC"""
        self.base_url = 'http://some_url'
        self.imc_token = 'some_token'
        self.request_timeout = 5

    def test_init(self):
        """Test method __init__ for APIClientIMC"""

        ### Run ###

        with patch('apiclient.APIClient.__init__') as super_init_mock, \
                patch('api_clients.api_client_imc.apiclient.HeaderAuthentication'
                      ) as header_authentication_mock:
            self.client = APIClientIMC(
                base_url=self.base_url,
                imc_token=self.imc_token,
                request_timeout=self.request_timeout
            )

        ### Assertions ###

        super_init_mock.assert_called_once_with(
            authentication_method=header_authentication_mock.return_value,
            response_handler=apiclient.JsonResponseHandler,
            request_formatter=apiclient.JsonRequestFormatter
        )
        header_authentication_mock.assert_called_once_with(token=self.imc_token, scheme='Token')
        self.assertEqual(self.client._request_timeout, self.request_timeout)
        self.assertEqual(self.client._base_url, self.base_url)


class TestGetEnpoint(TestAPIClientIMC):
    """Class for testing method _get_endpoint()"""

    def setUp(self) -> None:
        """Setup for test method _get_endpoint()"""
        ### SetUp ###

        super().setUp()

        ### Run ###

        self.client = APIClientIMC(
            base_url=self.base_url,
            imc_token=self.imc_token,
            request_timeout=self.request_timeout
        )

    def test__get_endpoint(self):
        """Test of method _get_endpoint() for APIClientIMC"""

        ### SetUp ###

        sub_url = 'some/sub/url'

        ### Run ###

        result = self.client._get_endpoint(sub_url)

        ### Assertions ###
        self.assertIsInstance(result, str)
        self.assertEqual(result, f'{self.base_url}/{sub_url}')


class TestGetRequestTimeout(TestAPIClientIMC):
    """Class for testing method get_request_timeout()"""

    def setUp(self) -> None:
        """Setup for test method get_request_timeout()"""
        ### SetUp ###

        super().setUp()

        ### Run ###

        self.client = APIClientIMC(
            base_url=self.base_url,
            imc_token=self.imc_token,
            request_timeout=self.request_timeout
        )

    def test_get_request_timeout(self):
        """Test method get_request_timeout"""
        ### Run ###

        result = self.client.get_request_timeout()

        ### Assertions ###
        self.assertIsInstance(result, float)
        self.assertEqual(result, 5.0)


class TestGetFelixDataByMbdSn(TestAPIClientIMC):
    """Class for testing method get_felix_data_by_mbd_sn("""

    def setUp(self) -> None:
        """Setup for test method get_felix_data_by_mbd_sn()"""
        ### SetUp ###

        super().setUp()

        ### Run ###
        with patch('api_clients.api_client_imc._IMCEndpoints') as imc_urls_mock:
            imc_urls_mock.felix_data_by_mbd_sn.return_value = \
                'products/components/serial-number/{mbd_sn}/felix'
            self.client = APIClientIMC(
                base_url=self.base_url,
                imc_token=self.imc_token,
                request_timeout=self.request_timeout
            )

    def test_get_felix_data_by_mbd_sn(self):
        """Test method get_felix_data_by_mbd_sn()"""

        ### SetUp ###

        self.some_mbd_sn = 'some_mbd_sn'
        self.client.get = Mock(return_value={})

        ### Run ###

        result = self.client.get_felix_data_by_mbd_sn(self.some_mbd_sn)

        ### Assertions ###

        self.assertIsInstance(result, FelixData)
        self.assertEqual(dict(result).keys(), [
            'id', 'serial_number',
            'model_id', 'model_name', 'model_tech_name', 'model_article',
            'model_vendor_article', 'chassis_article'
        ])
