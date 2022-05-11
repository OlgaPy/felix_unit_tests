"""
Unit tests for "controllers.inventory_scanner.Disk" class
"""

import unittest

import objdict

from workers.utils.inventory_scanner import Disk


class TestDisk(unittest.TestCase):
    """
    Base class for "controllers.inventory_scanner.Disk" unit tests
    """

    def setUp(self) -> None:
        """Set up test."""
        self.data = objdict.ObjDict(
            id='id',
            claimed='claimed',
            handle='handle',
            description='description',
            product='product',
            physid='physid',
            businfo='businfo',
            logicalname='logicalname',
            dev='dev',
            version='version',
            serial='serial',
            units='units',
            size='size',
        )
        self.disk = Disk(objdict.ObjDict(self.data))


class TestInit(TestDisk):
    """
    Unit tests for "Disk.__init__" method
    """

    def test_creates_attrs(self):
        """
        Tests list of Disk instance attributes
        """
        ### Assertion ###

        self.assertEqual(self.data.id, self.disk.id)
        self.assertEqual(self.data.claimed, self.disk.claimed)
        self.assertEqual(self.data.handle, self.disk.handle)
        self.assertEqual(self.data.description, self.disk.description)
        self.assertEqual(self.data.product, self.disk.product)
        self.assertEqual(self.data.physid, self.disk.physid)
        self.assertEqual(self.data.businfo, self.disk.businfo)
        self.assertEqual(self.data.logicalname, self.disk.logicalname)
        self.assertEqual(self.data.dev, self.disk.dev)
        self.assertEqual(self.data.version, self.disk.version)
        self.assertEqual(self.data.serial, self.disk.serial)
        self.assertEqual(self.data.units, self.disk.units)
        self.assertEqual(self.data.size, self.disk.size)


class TestStr(TestDisk):
    """
    Unit tests for "Disk.__str__" method
    """

    def test_returns_string_representation(self):
        """
        Tests that string made up of "logicalname",
        "product" and "description" attribute
        values is returned
        """
        ### Setup ###

        self.disk.logicalname = 'logicalname'
        self.disk.product = 'product'
        self.disk.description = 'description'

        ### Run ###

        result = self.disk.__str__()

        ### Assertions ###

        self.assertEqual(f'{self.disk.logicalname} {self.disk.product} {self.disk.description}', result)


class TestPresent(TestDisk):
    """
    Unit tests for "Disk.present" property
    """

    def test_returns_true_if_product(self):
        """
        Tests that if "product" attribute is
        not None, True is returned
        """
        ### Setup ###

        self.disk.product = 'some product'

        ### Run ###

        result = self.disk.present

        ### Assertions ###

        self.assertIs(result, True)

    def test_returns_false_if_not_product(self):
        """
        Tests that if "product" attribute is
        None, False is returned
        """
        ### Setup ###

        self.disk.product = None

        ### Run ###

        result = self.disk.present

        ### Assertions ###

        self.assertIs(result, False)
