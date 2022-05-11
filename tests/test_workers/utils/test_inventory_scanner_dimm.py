"""
Unit tests for "controllers.inventory_scanner.DIMM" class
"""

import unittest

import objdict

from workers.utils.inventory_scanner import DIMM


class TestDIMM(unittest.TestCase):
    """
    Base class for "controllers.inventory_scanner.DIMM" unit tests
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
            serial='serial',
            slot='slot',
            units='units',
            size='size',
            width='width',
            clock='clock',
        )
        self.dimm = DIMM(objdict.ObjDict(self.data))


class TestInit(TestDIMM):
    """
    Unit tests for "DIMM.__init__" method
    """

    def test_creates_attrs(self):
        """
        Tests list of DIMM instance attributes
        """
        ### Assertion ###

        self.assertEqual(self.data.id, self.dimm.id)
        self.assertEqual(self.data.claimed, self.dimm.claimed)
        self.assertEqual(self.data.handle, self.dimm.handle)
        self.assertEqual(self.data.description, self.dimm.description)
        self.assertEqual(self.data.product, self.dimm.product)
        self.assertEqual(self.data.vendor, self.dimm.vendor)
        self.assertEqual(self.data.physid, self.dimm.physid)
        self.assertEqual(self.data.serial, self.dimm.serial)
        self.assertEqual(self.data.slot, self.dimm.slot)
        self.assertEqual(self.data.units, self.dimm.units)
        self.assertEqual(self.data.size, self.dimm.size)
        self.assertEqual(self.data.width, self.dimm.width)
        self.assertEqual(self.data.clock, self.dimm.clock)


class TestPresent(TestDIMM):
    """
    Unit tests for "DIMM.present" property
    """

    def test_returns_true_if_product(self):
        """
        Tests that if "product" attribute is
        not None, True is returned
        """
        ### Setup ###

        self.dimm.product = 'some product'

        ### Run ###

        result = self.dimm.present

        ### Assertions ###

        self.assertIs(result, True)

    def test_returns_false_if_not_product(self):
        """
        Tests that if "product" attribute is
        None, False is returned
        """
        ### Setup ###

        self.dimm.product = None

        ### Run ###

        result = self.dimm.present

        ### Assertions ###

        self.assertIs(result, False)


class TestStr(TestDIMM):
    """
    Unit tests for "DIMM.__str__" method
    """

    def test_returns_string_representation(self):
        """
        Tests that string made up of
        "slot", "vendor" and "product"
        attribute values is returned
        """
        ### Setup ###

        self.dimm.slot = 'slot'
        self.dimm.vendor = 'vendor'
        self.dimm.product = 'product'

        ### Run ###

        result = self.dimm.__str__()

        ### Assertions ###

        self.assertEqual(
            f'{self.dimm.slot} {self.dimm.vendor} {self.dimm.product} {self.dimm.serial} - {"cache" if self.dimm.cache else "memory"}',  
            result
        )
