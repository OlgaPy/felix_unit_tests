"""
Unit tests for "controllers.inventory_scanner.Interface" class
"""

import unittest
from unittest.mock import patch, Mock, call

import objdict

from workers.utils.inventory_scanner import Interface


class TestInterface(unittest.TestCase):
    """
    Base class for "controllers.inventory_scanner.Interface" unit tests
    """

    def setUp(self) -> None:
        """Set up test."""
        self.AddrInfo_mock = Mock()
        self.data = objdict.ObjDict(
            ifindex='ifindex',
            ifname='ifname',
            mtu='mtu',
            qdisc='qdisc',
            operstate='operstate',
            group='group',
            txqlen='txqlen',
            link_type='link_type',
            address='address',
            broadcast='broadcast',
            flags=['flag1', 'flag2'],
            addr_info=['info1', 'info2']
        )
        with patch('workers.utils.inventory_scanner.AddrInfo', self.AddrInfo_mock):
            self.interface = Interface(objdict.ObjDict(self.data))


class TestInit(TestInterface):
    """
    Unit tests for "Interface.__init__" method
    """

    def test_creates_attrs(self):
        """
        Tests list of Disk instance attributes
        """
        ### Assertion ###

        self.assertEqual(self.data.ifindex, self.interface.ifindex)
        self.assertEqual(self.data.ifname, self.interface.ifname)
        self.assertEqual(self.data.mtu, self.interface.mtu)
        self.assertEqual(self.data.qdisc, self.interface.qdisc)
        self.assertEqual(self.data.operstate, self.interface.operstate)
        self.assertEqual(self.data.group, self.interface.group)
        self.assertEqual(self.data.txqlen, self.interface.txqlen)
        self.assertEqual(self.data.link_type, self.interface.link_type)
        self.assertEqual(self.data.address, self.interface.address)
        self.assertEqual(self.data.broadcast, self.interface.broadcast)
        self.assertEqual([flag for flag in self.data.flags], self.interface.flags)
        self.assertEqual([self.AddrInfo_mock.return_value for _ in self.data.addr_info], self.interface.addr_info)
        self.AddrInfo_mock.assert_has_calls([
            call(info) for info in self.data.addr_info
        ])


class TestStr(TestInterface):
    """
    Unit tests for "Interface.__str__" method
    """

    def test_returns_string_representation(self):
        """
        Tests that string made up of "ifname",
        "address", "link_type" and "operstate"
        attribute values is returned
        """
        ### Setup ###

        self.interface.ifname = 'ifname'
        self.interface.address = 'address'
        self.interface.link_type = 'link_type'
        self.interface.operstate = 'operstate'
        self.interface.businfo = 'businfo'
        self.interface.product = 'product'

        ### Run ###

        result = self.interface.__str__()

        ### Assertions ###

        self.assertEqual(
            f'{self.interface.ifname} | {self.interface.address} | {self.interface.link_type} | {self.interface.operstate} | {self.interface.businfo} | {self.interface.product}',  
            result
        )


class TestPresent(TestInterface):
    """
    Unit tests for "Interface.present" property
    """

    def test_returns_true(self):
        """
        Tests that True is returned
        """
        ### Run ###

        result = self.interface.present

        ### Assertions ###

        self.assertIs(result, True)


class TestFiber(TestInterface):
    """
    Unit tests for "Interface.fiber" property
    """

    def test_true_if_fibre_in_supported_ports(self):
        """
        Test that if "FIBRE" is in "supported_ports"
        attribute value, True is returned
        """
        ### Setup ###

        self.interface.supported_ports = 'FIBRE glass'

        ### Run ###

        result = self.interface.fiber

        ### Assertions ###

        self.assertIs(result, True)

    def test_false_if_fibre_not_in_supported_ports(self):
        """
        Test that if "FIBRE" is not in "supported_ports"
        attribute value, False is returned
        """
        ### Setup ###

        self.interface.supported_ports = 'twisted pair'

        ### Run ###

        result = self.interface.fiber

        ### Assertions ###

        self.assertIs(result, False)


class TestTwistedPair(TestInterface):
    """
    Unit tests for "Interface.twisted_pair" property
    """

    def test_true_if_tp_in_supported_ports(self):
        """
        Test that if "TP" is in "supported_ports"
        attribute value, True is returned
        """
        ### Setup ###

        self.interface.supported_ports = 'TP link'

        ### Run ###

        result = self.interface.twisted_pair

        ### Assertions ###

        self.assertIs(result, True)

    def test_false_if_tp_not_in_supported_ports(self):
        """
        Test that if "TP" is not in "supported_ports"
        attribute value, False is returned
        """
        ### Setup ###

        self.interface.supported_ports = 'fibre glass'

        ### Run ###

        result = self.interface.twisted_pair

        ### Assertions ###

        self.assertIs(result, False)


class TestLink(TestInterface):
    """
    Unit tests for "Interface.link" property
    """

    def test_true_if_link_is_detected(self):
        """
        Test that if "link_detected" attribute
        value is "yes", True is returned
        """
        ### Setup ###

        self.interface.link_detected = 'yes'

        ### Run ###

        result = self.interface.link

        ### Assertions ###

        self.assertIs(result, True)

    def test_false_if_link_is_not_detected(self):
        """
        Test that if "link_detected" attribute
        value is not "yes", False is returned
        """
        ### Setup ###

        self.interface.link_detected = 'no'

        ### Run ###

        result = self.interface.link

        ### Assertions ###

        self.assertIs(result, False)


class TestAddSupportedPorts(TestInterface):
    """
    Unit tests for "Interface.add_supported_ports" property
    """

    def test_sets_supported_ports(self):
        """
        Tests that provided data is set
        to "supported_ports" attribute
        """
        ### Setup ###

        data = ['twp']

        ### Run ###

        self.interface.add_supported_ports(data)

        ### Assertions ###

        self.assertEqual(data, self.interface.supported_ports)
