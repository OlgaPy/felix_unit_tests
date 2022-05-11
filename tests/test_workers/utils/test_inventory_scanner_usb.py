"""
Unit tests for "controllers.inventory_scanner.USB" class
"""

import unittest

import objdict

from workers.utils.inventory_scanner import USB


class TestUSB(unittest.TestCase):
    """
    Base class for "controllers.inventory_scanner.USB" unit tests
    """

    def setUp(self) -> None:
        """Set up test."""
        self.data = objdict.ObjDict(
            claimed='claimed',
            handle='handle',
            product='product',
            vendor='vendor',
            businfo='businfo'
        )
        self.usb = USB(objdict.ObjDict(self.data))


class TestInit(TestUSB):
    """
    Unit tests for "USB.__init__" method
    """

    def test_creates_attrs(self):
        """
        Tests list of USB attributes
        """
        ### Assertion ###

        self.assertEqual(self.data.claimed, self.usb.claimed)
        self.assertEqual(self.data.handle, self.usb.handle)
        self.assertEqual(self.data.product, self.usb.product)
        self.assertEqual(self.data.vendor, self.usb.vendor)
        self.assertEqual(self.data.businfo, self.usb.businfo)


class TestStr(TestUSB):
    """
    Unit tests for "USB.__str__" method
    """

    def test_returns_string_representation(self):
        """Test representation method."""
        ### Setup ###

        self.usb.handle = 'handle'
        self.usb.vendor = 'vendor'
        self.usb.product = 'product'

        ### Run ###

        result = self.usb.__str__()

        ### Assertions ###

        self.assertEqual(f'{self.usb.handle} {self.usb.vendor} {self.usb.product}', result)


class TestPresent(TestUSB):
    """
    Unit tests for "USB.present" property
    """

    def test_property(self):
        """Test property execution."""
        ### Run ###

        for self.usb.claimed in (False, True):
            with self.subTest(claimed_value=self.usb.claimed):

                ### Assertions ###

                self.assertIs(self.usb.present, self.usb.claimed)
