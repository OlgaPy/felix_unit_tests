"""
Unit tests for "controllers.inventory_scanner.CPU" class
"""

import unittest

import objdict

from workers.utils.inventory_scanner import CPU


class TestCPU(unittest.TestCase):
    """
    Base class for "controllers.inventory_scanner.CPU" unit tests
    """

    def setUp(self) -> None:
        """Set up test."""
        self.data = objdict.ObjDict(
            id='id',
            claimed='claimed',
            handle='handle',
            description='description',
            product='product',
            vendor='vendor',
            physid='physid',
            businfo='businfo',
            version='version',
            slot='slot',
            units='units',
            size='size',
            capacity='capacity',
            width='width',
            clock='clock',
            configuration=objdict.ObjDict,
        )
        self.cpu = CPU(objdict.ObjDict(self.data))


class TestInit(TestCPU):
    """
    Unit tests for "CPU.__init__" method
    """

    def test_creates_attrs(self):
        """
        Tests list of CPU instance attributes
        """
        ### Assertion ###

        self.assertEqual(self.data.id, self.cpu.id)
        self.assertEqual(self.data.claimed, self.cpu.claimed)
        self.assertEqual(self.data.handle, self.cpu.handle)
        self.assertEqual(self.data.description, self.cpu.description)
        self.assertEqual(self.data.product, self.cpu.product)
        self.assertEqual(self.data.vendor, self.cpu.vendor)
        self.assertEqual(self.data.physid, self.cpu.physid)
        self.assertEqual(self.data.businfo, self.cpu.businfo)
        self.assertEqual(self.data.version, self.cpu.version)
        self.assertEqual(self.data.slot, self.cpu.slot)
        self.assertEqual(self.data.units, self.cpu.units)
        self.assertEqual(self.data.size, self.cpu.size)
        self.assertEqual(self.data.capacity, self.cpu.capacity)
        self.assertEqual(self.data.width, self.cpu.width)
        self.assertEqual(self.data.clock, self.cpu.clock)
        self.assertEqual(self.data.configuration, self.cpu.configuration)


class TestPresent(TestCPU):
    """
    Unit tests for "CPU.present" property
    """

    def test_returns_true_if_product(self):
        """
        Tests that if "product" attribute is
        not None, True is returned
        """
        ### Setup ###

        self.cpu.product = 'some product'

        ### Run ###

        result = self.cpu.present

        ### Assertions ###

        self.assertIs(result, True)

    def test_returns_false_if_not_product(self):
        """
        Tests that if "product" attribute is
        None, False is returned
        """
        ### Setup ###

        self.cpu.product = None

        ### Run ###

        result = self.cpu.present

        ### Assertions ###

        self.assertIs(result, False)


class TestCores(TestCPU):
    """
    Unit tests for "CPU.cores" property
    """

    def test_returns_cores_number(self):
        """
        Tests that if cores data is available,
        number of cores is returned
        """
        ### Setup ###

        self.cpu.configuration = objdict.ObjDict(cores='4')

        ### Run ###

        result = self.cpu.cores

        ### Assertions ###

        self.assertEqual(4, result)

    def test_returns_none_if_no_configuration_data(self):
        """
        Tests that if "configuration" attribute value
        is None, None is returned
        """
        ### Setup ###

        self.cpu.configuration = None

        ### Run ###

        result = self.cpu.cores

        ### Assertions ###

        self.assertIsNone(result)

    def test_returns_none_if_no_cores_field_in_configuration_data(self):
        """
        Tests that if there is no "cores" field in
        "configuration" data, None is returned
        """
        ### Setup ###

        self.cpu.configuration = objdict.ObjDict()

        ### Run ###

        result = self.cpu.cores

        ### Assertions ###

        self.assertIsNone(result)

    def test_returns_none_if_no_cores_data_in_configuration_data(self):
        """
        Tests that if "cores" field in configuration
        data is None, None is returned
        """
        ### Setup ###

        self.cpu.configuration = objdict.ObjDict(cores=None)

        ### Run ###

        result = self.cpu.cores

        ### Assertions ###

        self.assertIsNone(result)


class TestEnabledCores(TestCPU):
    """
    Unit tests for "CPU.enabled_cores" property
    """

    def test_returns_enabled_cores_number(self):
        """
        Tests that if enabled cores data is available,
        number of enabled cores is returned
        """
        ### Setup ###

        self.cpu.configuration = objdict.ObjDict(enabledcores='4')

        ### Run ###

        result = self.cpu.enabled_cores

        ### Assertions ###

        self.assertEqual(4, result)

    def test_returns_none_if_no_configuration_data(self):
        """
        Tests that if "configuration" attribute value
        is None, None is returned
        """
        ### Setup ###

        self.cpu.configuration = None

        ### Run ###

        result = self.cpu.enabled_cores

        ### Assertions ###

        self.assertIsNone(result)

    def test_returns_none_if_no_enabledcores_field_in_configuration_data(self):
        """
        Tests that if there is no "enabledcores" field in
        "configuration" data, None is returned
        """
        ### Setup ###

        self.cpu.configuration = objdict.ObjDict()

        ### Run ###

        result = self.cpu.enabled_cores

        ### Assertions ###

        self.assertIsNone(result)

    def test_returns_none_if_no_enabledcores_data_in_configuration_data(self):
        """
        Tests that if "enabledcores" field in
        configuration data is None, None is returned
        """
        ### Setup ###

        self.cpu.configuration = objdict.ObjDict(enabledcores=None)

        ### Run ###

        result = self.cpu.enabled_cores

        ### Assertions ###

        self.assertIsNone(result)


class TestStr(TestCPU):
    """
    Unit tests for "CPU.__str__" method
    """

    def test_returns_string_representation(self):
        """
        Tests that string made up of
        "slot", "vendor" and "product"
        attribute values is returned
        """
        ### Setup ###

        self.cpu.slot = 'slot'
        self.cpu.vendor = 'vendor'
        self.cpu.product = 'product'

        ### Run ###

        result = self.cpu.__str__()

        ### Assertions ###

        self.assertEqual(f'{self.cpu.slot} {self.cpu.vendor} {self.cpu.product}', result)
