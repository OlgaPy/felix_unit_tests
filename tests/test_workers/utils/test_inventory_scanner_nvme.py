"""
Unit tests for "controllers.inventory_scanner.NVMe" class
"""

import unittest

import objdict

from workers.utils.inventory_scanner import NVMe


class TestNVMe(unittest.TestCase):
    """
    Base class for "controllers.inventory_scanner.NVMe" unit tests
    """

    def setUp(self) -> None:
        """Set up test."""
        self.data = objdict.ObjDict(
            namespace='namespace',
            device_path='device_path',
            firmware='firmware',
            index='index',
            model_number='model_number',
            product_name='product_name',
            serial_number='serial_number',
            used_bytes='used_bytes',
            maximum_lba='maximum_lba',
            physical_size='physical_size',
            sector_size='sector_size',
        )
        self.nvme = NVMe(objdict.ObjDict(self.data))


class TestInit(TestNVMe):
    """
    Unit tests for "NVMe.__init__" method
    """

    def test_creates_attrs(self):
        """
        Tests list of NVMe instance attributes
        """
        ### Assertion ###

        self.assertEqual(self.data.namespace, self.nvme.namespace)
        self.assertEqual(self.data.device_path, self.nvme.device_path)
        self.assertEqual(self.data.firmware, self.nvme.firmware)
        self.assertEqual(self.data.index, self.nvme.index)
        self.assertEqual(self.data.model_number, self.nvme.model_number)
        self.assertEqual(self.data.product_name, self.nvme.product_name)
        self.assertEqual(self.data.serial_number, self.nvme.serial_number)
        self.assertEqual(self.data.used_bytes, self.nvme.used_bytes)
        self.assertEqual(self.data.maximum_lba, self.nvme.maximum_lba)
        self.assertEqual(self.data.physical_size, self.nvme.physical_size)
        self.assertEqual(self.data.sector_size, self.nvme.sector_size)


class TestStr(TestNVMe):
    """
    Unit tests for "NVMe.__str__" method
    """

    def test_returns_string_representation(self):
        """
        Tests that string made up of "device_path",
        "model_number" and "product_name" attribute
        values is returned
        """
        ### Setup ###

        self.nvme.device_path = 'device_path'
        self.nvme.model_number = 'model_number'
        self.nvme.product_name = 'product_name'

        ### Run ###

        result = self.nvme.__str__()

        ### Assertions ###

        self.assertEqual(f'{self.nvme.device_path} {self.nvme.model_number} {self.nvme.product_name}', result)


class TestPresent(TestNVMe):
    """
    Unit tests for "NVMe.present" property
    """

    def test_returns_true(self):
        """
        Tests that True is returned
        """
        ### Run ###

        result = self.nvme.present

        ### Assertions ###

        self.assertIs(result, True)
