"""
Unit tests for "controllers.inventory_scanner.AddrInfo" class
"""

import unittest

import objdict

from workers.utils.inventory_scanner import AddrInfo


class TestAddrInfo(unittest.TestCase):
    """
    Base class for "controllers.inventory_scanner.AddrInfo" unit tests
    """

    def setUp(self) -> None:
        """Set up test."""
        self.data = objdict.ObjDict(
            family='family',
            local='local',
            prefixlen='prefixlen',
            broadcast='broadcast',
            scope='scope',
            secondary='secondary',
            label='label',
            valid_life_time='valid_life_time',
            preferred_life_time='preferred_life_time'
        )
        self.addr_info = AddrInfo(objdict.ObjDict(self.data))


class TestInit(TestAddrInfo):
    """
    Unit tests for "AddrInfo.__init__" method
    """

    def test_creates_attrs(self):
        """
        Tests list of AddrInfo instance attributes
        """
        ### Assertion ###

        self.assertEqual(self.data.family, self.addr_info.family)
        self.assertEqual(self.data.local, self.addr_info.local)
        self.assertEqual(self.data.prefixlen, self.addr_info.prefixlen)
        self.assertEqual(self.data.broadcast, self.addr_info.broadcast)
        self.assertEqual(self.data.scope, self.addr_info.scope)
        self.assertEqual(self.data.secondary, self.addr_info.secondary)
        self.assertEqual(self.data.label, self.addr_info.label)
        self.assertEqual(self.data.valid_life_time, self.addr_info.valid_life_time)
        self.assertEqual(self.data.preferred_life_time, self.addr_info.preferred_life_time)


class TestStr(TestAddrInfo):
    """
    Unit tests for "AddrInfoscope.__str__" method
    """

    def test_returns_string_representation(self):
        """
        Tests that string made up of "family",
        "label" and "" attribute values is returned
        """
        ### Setup ###

        self.addr_info.scope = 'scope'
        self.addr_info.family = 'family'
        self.addr_info.label = 'label'

        ### Run ###

        result = self.addr_info.__str__()

        ### Assertions ###

        self.assertEqual(f'{self.addr_info.scope} {self.addr_info.family} {self.addr_info.label}', result)


class TestPresent(TestAddrInfo):
    """
    Unit tests for "AddrInfo.present" property
    """

    def test_returns_true(self):
        """
        Tests that True is returned
        """
        ### Run ###

        result = self.addr_info.present

        ### Assertions ###

        self.assertIs(result, True)
