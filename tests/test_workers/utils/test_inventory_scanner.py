"""
Unit tests for "workers.utils.inventory_scanner.InventoryScanner" class
"""
import json
import unittest
from unittest.mock import patch, Mock, call, PropertyMock, mock_open

import objdict
from workers.utils.inventory_scanner import _lshw_extract, InventoryScanner


class TestInventoryScanner(unittest.TestCase):
    """
    Base class for "workers.utils.inventory_scanner.InventoryScanner" unit tests
    """

    def setUp(self) -> None:
        """Set up test."""
        with patch('workers.utils.inventory_scanner.logger'), \
             patch('workers.utils.inventory_scanner.ControllerFelix.motherboard_serial_number', PropertyMock()):
            self.scanner = InventoryScanner(motherboard=Mock(), printer=Mock(), controller=Mock())


class TestInit(TestInventoryScanner):
    """
    Unit tests for "InventoryScanner.__init__" method
    """

    def test_set_instance_attrs(self):
        """
        Tests that instance attributes
        are set during initialization
        """
        ### Assertions ###

        self.assertIsNone(self.scanner._nvme_list)
        self.assertIsNone(self.scanner._lshw)
        self.assertIsNone(self.scanner._ip)
        self.assertIsNone(self.scanner._pci_scanner)
        self.assertEqual([], self.scanner._dimms)
        self.assertEqual([], self.scanner._cpus)
        self.assertEqual([], self.scanner._nvmes)
        self.assertEqual([], self.scanner._pcis)
        self.assertEqual([], self.scanner._sata)
        self.assertEqual([], self.scanner._usb)
        self.assertEqual([], self.scanner._interfaces)
        self.assertEqual([], self.scanner._fibers)
        self.assertEqual([], self.scanner._twisted_pairs)


class TestExecScan(TestInventoryScanner):
    """
    Unit tests for "InventoryScanner.exec_scan" method
    """

    def test_calls_scan_methods(self):
        """
        Tests that "power_on_host", "_get_lshw",
        "get_pci_scanner" and "_ifaces" methods are called
        """
        ### Setup ###

        self.scanner.power_on_host = Mock()
        self.scanner._get_lshw = Mock()
        self.scanner.get_pci_scanner = Mock()
        self.scanner._ifaces = Mock()

        ### Run ###

        self.scanner.exec_scan()

        ### Assertions ###

        self.scanner.power_on_host.asssert_called_once()
        self.scanner._get_lshw.asssert_called_once()
        self.scanner.get_pci_scanner.asssert_called_once()
        self.scanner._ifaces.asssert_called_once()


class TestGetNvmeList(TestInventoryScanner):
    """
    Unit tests for "InventoryScanner._get_nvme_list" method
    """

    def setUp(self) -> None:
        """Set up test."""
        super(TestGetNvmeList, self).setUp()
        self.nvme_list = {'1': 'nvme1', '2': 'nvme2', '3': 'nvme3'}
        self.data = json.dumps(self.nvme_list)
        self.open_mock = mock_open(read_data=self.data)

        self.remote_nvme_list_path = '/tmp/nvme_list.json'
        self.local_nvme_list_path = f'/tmp/{self.scanner.controller.motherboard_serial_number}_nvme_list.json'

    def test_execs_nvme_list_cmd(self):
        """
        Tests that "nvme list" command
        is executed on host
        """
        ### Run ###

        with patch('workers.utils.inventory_scanner.open', self.open_mock):
            self.scanner._get_nvme_list()

        ### Assertions ###

        self.scanner.controller.host.run_command.assert_called_once_with(
            f'nvme list -o json > {self.remote_nvme_list_path}',
            suppress_logs=True)

    def test_copies_file_from_host(self):
        """
        Tests that file with "nvme list" command
        output is copied from host
        """
        ### Run ###

        with patch('workers.utils.inventory_scanner.open', self.open_mock):
            self.scanner._get_nvme_list()

        ### Assertions ###

        self.scanner.controller.host.copy_from(
            remote_path=self.remote_nvme_list_path, local_path=self.local_nvme_list_path
        )

    def test_parses_output_and_returns_nvme_list(self):
        """
        Test that ObjDict is created from "nvme list"
        command output and returned
        """
        ### Run ###

        with patch('workers.utils.inventory_scanner.open', self.open_mock):
            result = self.scanner._get_nvme_list()

        ### Assertions ###

        self.open_mock.assert_called_once_with(self.local_nvme_list_path)
        self.assertEqual(objdict.ObjDict(self.data), result)
        self.scanner.logger.info.assert_called_once_with('Extracting nvme list info from host')
        self.scanner.logger.success.assert_called_once_with('lshw nvme list extracted')

    def test_returns_stored_nvme_list(self):
        """
        Tests that if originally "_nvme_list"
        attribute value is not None, it is returned
        """
        ### Setup ###

        nvme_list = Mock()
        self.scanner._nvme_list = nvme_list

        ### Run ###

        with patch('workers.utils.inventory_scanner.open', self.open_mock):
            result = self.scanner._get_nvme_list()

        ### Assertions ###

        self.assertEqual(nvme_list, result)
        self.scanner.controller.host.run_command.assert_not_called()
        self.scanner.controller.host.copy_from.assert_not_called()
        self.open_mock.assert_not_called()
        self.scanner.logger.info().assert_not_called()
        self.scanner.logger.success.assert_not_called()
        self.assertEqual(nvme_list, self.scanner._nvme_list)


class TestGetIp(TestInventoryScanner):
    """
    Unit tests for "InventoryScanner._get_ip" method
    """

    def setUp(self) -> None:
        """Set up test."""
        super(TestGetIp, self).setUp()
        self.ip_list = {'1': 'ip1', '2': 'ip2', '3': 'ip3'}
        self.data = json.dumps(self.ip_list)
        self.open_mock = mock_open(read_data=self.data)

        self.remote_ip_path = '/tmp/ip.json'
        self.local_ip_path = f'/tmp/{self.scanner.controller.motherboard_serial_number}_ip.json'

    def test_execs_ip_cmd(self):
        """
        Tests that "ip -j a" command
        is executed on host
        """
        ### Run ###

        with patch('workers.utils.inventory_scanner.open', self.open_mock):
            self.scanner._get_ip()

        ### Assertions ###

        self.scanner.controller.host.run_command.assert_called_once_with(
            command=f"""echo '{{"interfaces":' $(ip -j a) '}}' > {self.remote_ip_path}""",
            suppress_logs=True)

    def test_copies_file_from_host(self):
        """
        Tests that file with "ip -j a" command
        output is copied from host
        """
        ### Run ###

        with patch('workers.utils.inventory_scanner.open', self.open_mock):
            self.scanner._get_ip()

        ### Assertions ###

        self.scanner.controller.host.copy_from(remote_path=self.remote_ip_path, local_path=self.local_ip_path)

    def test_parses_output_and_returns_ip_list(self):
        """
        Test that ObjDict is created with "ip -j a"
        command output and returned
        """
        ### Run ###

        with patch('workers.utils.inventory_scanner.open', self.open_mock):
            result = self.scanner._get_ip()

        ### Assertions ###

        self.open_mock.assert_called_once_with(self.local_ip_path)
        self.assertEqual(objdict.ObjDict(self.data), result)
        self.scanner.logger.info.assert_called_once_with('Extracting ip info from host')
        self.scanner.logger.success.assert_called_once_with('ip info extracted')

    def test_returns_stored_ip_list(self):
        """
        Tests that if original "_ip" attribute
        value is not None, it is returned
        """
        ### Setup ###

        ip_list = Mock()
        self.scanner._ip = ip_list

        ### Run ###

        with patch('workers.utils.inventory_scanner.open', self.open_mock):
            result = self.scanner._get_ip()

        ### Assertions ###

        self.assertEqual(ip_list, result)
        self.scanner.controller.host.run_command.assert_not_called()
        self.scanner.controller.host.copy_from.assert_not_called()
        self.open_mock.assert_not_called()
        self.scanner.logger.info.assert_not_called()
        self.scanner.logger.success.assert_not_called()
        self.assertEqual(ip_list, self.scanner._ip)


class TestGetLshw(TestInventoryScanner):
    """
    Unit tests for "InventoryScanner._get_lshw" method
    """

    def setUp(self) -> None:
        """Set up test."""
        super(TestGetLshw, self).setUp()
        self.hw_list = {'1': 'hw1', '2': 'hw2', '3': 'hw3'}
        self.data = json.dumps(self.hw_list)
        self.open_mock = mock_open(read_data=self.data)

        self.remote_lshw_path = '/tmp/lshw.json'
        self.local_lshw_path = f'/tmp/{self.scanner.controller.motherboard_serial_number}_lshw.json'

    def test_execs_lshw_cmd(self):
        """
        Tests that "lshw" command
        is executed on host
        """
        ### Run ###

        with patch('workers.utils.inventory_scanner.open', self.open_mock):
            self.scanner._get_lshw()

        ### Assertions ###

        self.scanner.controller.host.run_command.assert_called_once_with(
            f'lshw -json > {self.remote_lshw_path}',
            suppress_logs=True)

    def test_copies_file_from_host(self):
        """
        Tests that file with "lshw" command
        output is copied from host
        """
        ### Run ###

        with patch('workers.utils.inventory_scanner.open', self.open_mock):
            self.scanner._get_lshw()

        ### Assertions ###

        self.scanner.controller.host.copy_from(remote_path=self.remote_lshw_path, local_path=self.local_lshw_path)

    def test_parses_output_and_returns_hw_list(self):
        """
        Test that ObjDict is created with "lshw"
        command output and returned
        """
        ### Run ###

        with patch('workers.utils.inventory_scanner.open', self.open_mock):
            result = self.scanner._get_lshw()

        ### Assertions ###

        self.open_mock.assert_called_once_with(self.local_lshw_path)
        self.assertEqual(objdict.ObjDict(self.data), result)
        self.scanner.logger.info.assert_called_once_with('Extracting lshw info from host')
        self.scanner.logger.success.assert_called_once_with('lshw info extracted')

    def test_returns_stored_hw_list(self):
        """
        Tests that if original "_lshw" attribute
        value is not None, it is returned
        """
        ### Setup ###

        hw_list = Mock()
        self.scanner._lshw = hw_list

        ### Run ###

        with patch('workers.utils.inventory_scanner.open', self.open_mock):
            result = self.scanner._get_lshw()

        ### Assertions ###

        self.assertEqual(hw_list, result)
        self.scanner.controller.host.run_command.assert_not_called()
        self.scanner.controller.host.copy_from.assert_not_called()
        self.open_mock.assert_not_called()
        self.scanner.logger.info.assert_not_called()
        self.scanner.logger.success.assert_not_called()
        self.assertEqual(hw_list, self.scanner._lshw)


@patch('workers.utils.inventory_scanner.pylspci')
@patch('workers.utils.inventory_scanner.settings')
class TestGetPciScanner(TestInventoryScanner):
    """
    Unit tests for "InventoryScanner.get_pci_scanner" method
    """

    def test_creates_and_returns_pci_scanner(self, settings_mock, pylspci_mock):
        """
        Tests that "pylspci.ScannerPCI" is
        created and returned
        """
        ### Setup ###

        self.scanner._pci_scanner = None

        ### Run ###

        result = self.scanner.get_pci_scanner()

        ### Assertions ###

        pylspci_mock.ScannerPCI.assert_called_once_with(
            ip=self.scanner.controller.host.ip,
            login=settings_mock.Felix.host_login,
            password=settings_mock.Felix.host_password
        )
        self.assertIs(result, pylspci_mock.ScannerPCI.return_value)
        self.scanner.logger.info.assert_called_once_with('Extracting lspci info from host')
        self.scanner.logger.success.assert_called_once_with('lspci info extracted')

    def test_returns_stored_pci_scanner(self, settings_mock, pylspci_mock):
        """
        Tests that if originally "_pci_scanner"
        attribute value is not None, it's returned
        """
        ### Setup ###

        pci_scanner = Mock()
        self.scanner._pci_scanner = pci_scanner

        ### Run ###

        result = self.scanner.get_pci_scanner()

        ### Assertions ###

        self.assertIs(result, pci_scanner)
        pylspci_mock.ScannerPCI.assert_not_called()
        self.scanner.logger.info.assert_not_called()
        self.scanner.logger.success.assert_not_called()
        self.assertIs(self.scanner._pci_scanner, pci_scanner)


@patch('workers.utils.inventory_scanner.DIMM')
@patch('workers.utils.inventory_scanner._lshw_extract')
class TestDimms(TestInventoryScanner):
    """
    Unit tests for "InventoryScanner.dimms" method
    """

    def setUp(self) -> None:
        """Set up test."""
        super(TestDimms, self).setUp()
        self.scanner._get_lshw = Mock()
        self.scanner._log_collection = Mock()

    def test_returns_dimms_list(self, lshw_extract_mock, DIMM_mock):
        """
        Tests that "DIMM"s instances are created
        from "lshw" output, stored in "_dimms"
        attribute and returned
        """
        ### Setup ###

        lshw_extract_mock.return_value = ['dimm1', 'dimm2', 'dimm3']

        ### Run ###

        result = self.scanner.dimms()

        ### Assertions ###

        self.assertEqual([DIMM_mock.return_value for _ in lshw_extract_mock.return_value], result)
        self.assertEqual([DIMM_mock.return_value for _ in lshw_extract_mock.return_value], self.scanner._dimms)
        DIMM_mock.assert_has_calls([call(dimm) for dimm in lshw_extract_mock.return_value])
        self.scanner._log_collection.assert_called_once_with(name='DIMMs', collection=result)

    def test_returns_stored_dimms(self, lshw_extract_mock, DIMM_mock):
        """
        Tests that if originally "_dimms" list
        is not empty list, it's returned
        """
        ### Setup ###

        dimms = ['dimm1', 'dimm2', 'dimm3']
        self.scanner._dimms = dimms

        ### Run ###

        result = self.scanner.dimms()

        ### Assertions ###

        self.assertIs(result, dimms)
        self.assertIs(self.scanner._dimms, dimms)
        self.scanner._get_lshw.assert_not_called()
        lshw_extract_mock.assert_not_called()
        DIMM_mock.assert_not_called()
        self.scanner.logger.info.assert_not_called()


@patch('workers.utils.inventory_scanner.CPU')
@patch('workers.utils.inventory_scanner._lshw_extract')
class TestCpus(TestInventoryScanner):
    """
    Unit tests for "InventoryScanner.cpus" method
    """

    def setUp(self) -> None:
        """Set up test."""
        super(TestCpus, self).setUp()
        self.scanner._get_lshw = Mock()
        self.scanner._log_collection = Mock()

    def test_returns_cpus_list(self, lshw_extract_mock, CPU_mock):
        """
        Tests that "CPU"s instances are created
        from "lshw" output, stored in "_cpu"
        attribute and returned
        """
        ### Setup ###

        lshw_extract_mock.return_value = ['cpu1', 'cpu2', 'cpu3']

        ### Run ###

        result = self.scanner.cpus()

        ### Assertions ###

        self.assertEqual([CPU_mock.return_value for _ in lshw_extract_mock.return_value], result)
        self.assertEqual([CPU_mock.return_value for _ in lshw_extract_mock.return_value], self.scanner._cpus)
        CPU_mock.assert_has_calls([call(cpu) for cpu in lshw_extract_mock.return_value])
        self.scanner._log_collection.assert_called_once_with(name='CPUs', collection=result)

    def test_returns_stored_cpus(self, lshw_extract_mock, CPU_mock):
        """
        Tests that if originally "_cpu" list
        is not empty list, it's returned
        """
        ### Setup ###

        cpus = ['cpu1', 'cpu2', 'dcpu']
        self.scanner._cpus = cpus

        ### Run ###

        result = self.scanner.cpus()

        ### Assertions ###

        self.assertIs(result, cpus)
        self.assertIs(self.scanner._cpus, cpus)
        self.scanner._get_lshw.assert_not_called()
        lshw_extract_mock.assert_not_called()
        CPU_mock.assert_not_called()
        self.scanner.logger.info.assert_not_called()


@patch('workers.utils.inventory_scanner.NVMe')
class TestNVMesDisks(TestInventoryScanner):
    """
    Unit tests for "InventoryScanner.nvmes_disks" method
    """

    def setUp(self) -> None:
        """Set up test."""
        super().setUp()
        self.scanner._get_nvme_list = Mock()
        self.scanner._log_collection = Mock()

    def test_returns_nvmes_list(self, NVMe_mock):
        """
        Tests that "NVMe"s instances are created,
        stored in "_nvmes" attribute and returned
        """
        ### Setup ###

        nvmes = ['nvme1', 'nvme2', 'nvme3']
        self.scanner._get_nvme_list.return_value.devices = nvmes

        ### Run ###

        result = self.scanner.nvmes_disks()

        ### Assertions ###

        self.assertEqual([NVMe_mock.return_value for _ in nvmes], result)
        self.assertEqual([NVMe_mock.return_value for _ in nvmes], self.scanner._nvmes)
        NVMe_mock.assert_has_calls([call(nvme) for nvme in nvmes])
        self.scanner._log_collection.assert_called_once_with(name='NVMe Disks', collection=result)

    def test_returns_stored_nvmes(self, NVMe_mock):
        """
        Tests that if originally "_nvmes" list
        is not empty list, it's returned
        """
        ### Setup ###

        nvmes = ['nvme1', 'nvme2', 'nvme3']
        self.scanner._nvmes = nvmes

        ### Run ###

        result = self.scanner.nvmes_disks()

        ### Assertions ###

        self.assertIs(result, nvmes)
        self.assertIs(self.scanner._nvmes, nvmes)
        self.scanner._get_nvme_list.assert_not_called()
        NVMe_mock.assert_not_called()
        self.scanner.logger.info.assert_not_called()


class TestPCIs(TestInventoryScanner):
    """
    Unit tests for "InventoryScanner.pcis" method
    """

    def setUp(self) -> None:
        """Set up test."""
        super(TestPCIs, self).setUp()
        self.scanner.get_pci_scanner = Mock()
        self.scanner._log_collection = Mock()

    def test_returns_pcis_list(self):
        """
        Tests that PCI devices list is got
        via pci_scanner, stored in "_nvmes"
        attribute and returned
        """
        ### Setup ###

        kw = {'key': 'value'}
        pcis = ['pci1', 'pci2', 'pci3']
        self.scanner.get_pci_scanner.return_value.select.return_value = pcis

        ### Run ###

        result = self.scanner.pcis(**kw)

        ### Assertions ###

        self.assertEqual([pci for pci in pcis], result)
        self.assertEqual([pci for pci in pcis], self.scanner._pcis)
        self.scanner.get_pci_scanner.return_value.select.assert_called_once_with(**kw)
        self.scanner._log_collection.assert_called_once_with(name='PCI Devices', collection=result, check_present=False)

    def test_returns_stored_pcis(self):
        """
        Tests that if originally "_pcis" list
        is not empty list, it's returned
        """
        ### Setup ###

        pcis = ['pci1', 'pci2', 'pci3']
        self.scanner._pcis = pcis

        ### Run ###

        result = self.scanner.pcis()

        ### Assertions ###

        self.assertIs(result, pcis)
        self.assertIs(self.scanner._pcis, pcis)
        self.scanner.get_pci_scanner.assert_not_called()
        self.scanner.logger.info.assert_not_called()


@patch('workers.utils.inventory_scanner.Disk')
@patch('workers.utils.inventory_scanner._lshw_extract')
class TestSata(TestInventoryScanner):
    """
    Unit tests for "InventoryScanner.sata_disks" method
    """

    def setUp(self) -> None:
        """Set up test."""
        super(TestSata, self).setUp()
        self.scanner._get_lshw = Mock()
        self.scanner._log_collection = Mock()

    def test_returns_disks_list(self, lshw_extract_mock, Disk_mock):
        """
        Tests that "Disk"s instances are created
        from "lshw" output, stored in "_sata"
        attribute and returned
        """
        ### Setup ###

        disk1 = {'class': 'some class', 'id': 'disk', 'businfo': '_scsi_'}
        disk2 = {'class': 'some class', 'id': 'disk', 'businfo': '_scsi_'}

        lshw_extract_mock.return_value = [
            objdict.ObjDict(cls='storage', id='1'),
            objdict.ObjDict(cls='storage', id='2', children=[
                objdict.ObjDict(disk1), objdict.ObjDict(disk2)
            ])
        ]

        ### Run ###

        result = self.scanner.sata_disks()

        ### Assertions ###

        self.assertEqual(result, [Disk_mock.return_value, Disk_mock.return_value])
        self.scanner._get_lshw.assert_called_once()
        lshw_extract_mock.assert_called_once_with(self.scanner._get_lshw.return_value, cls='storage', id='*scsi')
        Disk_mock.assert_has_calls([call(disk1), call(disk2)])
        self.scanner._log_collection.assert_called_once_with(name='SATA Disks', collection=result)

    def test_returns_stored_disks(self, lshw_extract_mock, Disk_mock):
        """
        Tests that if originally "_sata" list
        is not empty, it's returned
        """
        ### Setup ###

        disks = ['disk1', 'disk2', 'disk3']
        self.scanner._sata = disks

        ### Run ###

        result = self.scanner.sata_disks()

        ### Assertions ###

        self.assertIs(result, disks)
        self.assertIs(self.scanner._sata, disks)
        self.scanner._get_lshw.assert_not_called()
        lshw_extract_mock.assert_not_called()
        Disk_mock.assert_not_called()
        self.scanner.logger.info.assert_not_called()


@patch('workers.utils.inventory_scanner.Disk')
@patch('workers.utils.inventory_scanner._lshw_extract')
class TestScsi(TestInventoryScanner):
    """
    Unit tests for "InventoryScanner.scsi_disks" method
    """

    def setUp(self) -> None:
        """Set up test."""
        super().setUp()
        self.scanner._get_lshw = Mock()
        self.scanner._log_collection = Mock()

    def test_returns_disks_list(self, lshw_extract_mock, Disk_mock):
        """
        Tests that "Disk"s instances are created
        from "lshw" output, stored in "_scsi"
        attribute and returned
        """
        ### Setup ###

        disk1 = {'class': 'disk', 'id': 'disk', 'businfo': '_scsi_'}
        disk2 = {'class': 'disk', 'id': 'disk', 'businfo': '_scsi_'}

        lshw_extract_mock.return_value = [
            objdict.ObjDict(cls='storage', id='1'),
            objdict.ObjDict(cls='storage', id='2', children=[
                objdict.ObjDict(disk1), objdict.ObjDict(disk2)
            ])
        ]

        ### Run ###

        result = self.scanner.scsi_disks()

        ### Assertions ###

        self.assertEqual(result, [Disk_mock.return_value, Disk_mock.return_value])
        self.scanner._get_lshw.assert_called_once()
        lshw_extract_mock.assert_called_once_with(self.scanner._get_lshw.return_value, cls='storage',
                                                  id='storage', description='RAID bus controller')
        Disk_mock.assert_has_calls([call(disk1), call(disk2)])
        self.scanner._log_collection.assert_called_once_with(name='SCSI Disks', collection=result)

    def test_returns_stored_disks(self, lshw_extract_mock, Disk_mock):
        """
        Tests that if originally "_scsi" list
        is not empty, it's returned
        """
        ### Setup ###

        disks = ['disk1', 'disk2', 'disk3']
        self.scanner._scsi = disks

        ### Run ###

        result = self.scanner.scsi_disks()

        ### Assertions ###

        self.assertIs(result, disks)
        self.assertIs(self.scanner._scsi, disks)
        self.scanner._get_lshw.assert_not_called()
        lshw_extract_mock.assert_not_called()
        Disk_mock.assert_not_called()
        self.scanner.logger.info.assert_not_called()


@patch('workers.utils.inventory_scanner.USB')
@patch('workers.utils.inventory_scanner._lshw_extract')
class TestUsb(TestInventoryScanner):
    """
    Unit tests for "InventoryScanner.usbs" method
    """

    def setUp(self) -> None:
        """Set up test."""
        super().setUp()
        self.scanner._get_lshw = Mock()
        self.scanner._log_collection = Mock()

    def test_returns_usbs_list(self, lshw_extract_mock, USB_mock):
        """
        Tests that "USB"s instances are created
        from "lshw" output, stored in "_usb"
        attribute and returned
        """
        ### Setup ###

        usb1 = {'class': 'some class', 'id': 'usb', 'businfo': '_scsi_'}
        usb2 = {'class': 'some class', 'id': 'usb', 'businfo': '_scsi_'}

        lshw_extract_mock.return_value = [usb1, usb2]

        ### Run ###

        result = self.scanner.usbs()

        ### Assertions ###
        self.assertEqual([USB_mock.return_value, USB_mock.return_value], result)
        self.scanner._get_lshw.assert_called_once()
        lshw_extract_mock.assert_called_once_with(self.scanner._get_lshw.return_value, id='*usb', handle='*USB')
        USB_mock.assert_has_calls([call(usb1), call(usb2)])
        self.scanner._log_collection.assert_called_once_with(name='USBs', collection=result)

    def test_returns_stored_usbs(self, lshw_extract_mock, USB_mock):
        """
        Tests that if originally "_usb" list
        is not empty, it's returned
        """
        ### Setup ###

        usbs = ['usb1', 'usb2', 'usb3']
        self.scanner._usb = usbs

        ### Run ###

        result = self.scanner.usbs()

        ### Assertions ###

        self.assertIs(result, usbs)
        self.assertIs(self.scanner._usb, usbs)
        self.scanner._get_lshw.assert_not_called()
        lshw_extract_mock.assert_not_called()
        USB_mock.assert_not_called()
        self.scanner.logger.info.assert_not_called()


@patch('workers.utils.inventory_scanner._lshw_extract')
@patch('workers.utils.inventory_scanner.Interface')
class TestIfaces(TestInventoryScanner):
    """
    Unit tests for "InventoryScanner._ifaces" method
    """

    def setUp(self) -> None:
        """Set up test."""
        super(TestIfaces, self).setUp()
        self.scanner._get_lshw = Mock()
        self.scanner._log_collection = Mock()

    def test_returns_ifaces_list(self, Interface_mock, lshw_extract_mock):
        """
        Tests that "Interface" instances are created
        from "lshw" output, stored in "_usb"
        attribute and returned
        """
        ### Setup ###

        ifaces = ['eth0', 'eth1']
        self.scanner._get_ip = Mock(return_value=Mock(interfaces=ifaces))
        iface_mock1 = Mock(ifname=ifaces[0])
        iface_mock2 = Mock(ifname=ifaces[1])
        Interface_mock.side_effect = (iface_mock1, iface_mock2)

        lshw_extract_mock.return_value = [
            objdict.ObjDict(logicalname=ifaces[0], product='some product', businfo='pci@0000:00:00.0'),
            objdict.ObjDict(logicalname=ifaces[1], product=None, businfo=None)
        ]

        output1 = ['Supported ports: [ TP ]', 'some data', 'Link detected: no']
        output2 = ['Supported ports: [ FIBER ]', 'some data', 'Link detected: yes']

        self.scanner.controller.host.run_command_ignore_fail.side_effect = (output1, output2)

        ### Run ###

        result = self.scanner._ifaces()

        ### Assertions ###

        self.assertEqual([iface_mock1, iface_mock2], result)
        self.assertEqual([iface_mock1, iface_mock2], self.scanner._interfaces)
        Interface_mock.assert_has_calls([call(iface) for iface in ifaces])
        self.scanner.controller.host.run_command_ignore_fail.assert_has_calls([
            call(command=f'ethtool {iface_mock1.ifname}', suppress_logs=True),
            call(command=f'ethtool {iface_mock2.ifname}', suppress_logs=True)
        ])
        iface_mock1.add_supported_ports.assert_called_once_with(data=['TP'])
        iface_mock2.add_supported_ports.assert_called_once_with(data=['FIBER'])
        self.assertEqual(iface_mock1.link_detected, 'no')
        self.assertEqual(iface_mock2.link_detected, 'yes')
        self.assertEqual(iface_mock1.product, 'some product')
        self.assertIsNone(iface_mock2.product)
        self.assertEqual(iface_mock1.businfo, 'pci@0000:00:00.0')
        self.assertIsNone(iface_mock2.businfo)
        lshw_extract_mock.assert_called_once_with(self.scanner._get_lshw(), id='*network')
        self.scanner._log_collection.assert_called_once_with(name='Network Interfaces', collection=result)

    def test_returns_stored_ifaces(self, Interface_mock, lshw_extract_mock):
        """
        Tests that if originally "_interfaces"
        list is not empty, it's returned
        """
        ### Setup ###

        ifaces = ['eth0', 'eth1']
        self.scanner._interfaces = ifaces

        ### Run ###

        result = self.scanner._ifaces()

        ### Assertions ###

        self.assertIs(result, ifaces)
        self.assertIs(self.scanner._interfaces, ifaces)
        Interface_mock.assert_not_called()
        self.scanner.controller.host.run_command_ignore_fail.assert_not_called()
        lshw_extract_mock.assert_not_called()
        self.scanner.logger.info.assert_not_called()


class TestTwistedPair(TestInventoryScanner):
    """
    Unit tests for "InventoryScanner.twisted_pairs" method
    """

    def setUp(self) -> None:
        """Set up test."""
        super().setUp()
        self.scanner._log_collection = Mock()

    def test_returns_twisted_pair_ifaces(self):
        """
        Tests that list interfaces with twisted
        pair type is saved in "_twisted_pair"
        attribute and returned
        """
        ### Setup ###

        ifaces = [Mock(twisted_pair=True), Mock(twisted_pair=False), Mock(twisted_pair=True)]
        self.scanner._ifaces = Mock(return_value=ifaces)

        ### Run ###

        result = self.scanner.twisted_pairs()

        ### Assertions ###

        self.assertEqual([ifaces[0], ifaces[2]], result)
        self.assertEqual([ifaces[0], ifaces[2]], self.scanner._twisted_pairs)
        self.scanner._log_collection.assert_called_once_with(name='Twisted Pair Adapters', collection=result)

    def test_returns_stored_twisted_pair_ifaces(self):
        """
        Tests that if originally "_twisted_pair"
        list is not empty, it's returned
        """
        ### Setup ###

        tps = ['tp1', 'tp2']
        self.scanner._twisted_pairs = tps
        self.scanner._ifaces = Mock()

        ### Run ###

        result = self.scanner.twisted_pairs()

        ### Assertions ###

        self.assertIs(result, tps)
        self.assertIs(self.scanner._twisted_pairs, tps)
        self.scanner._ifaces.assert_not_called()
        self.scanner.logger.info.assert_not_called()


class TestFibers(TestInventoryScanner):
    """
    Unit tests for "InventoryScanner.fibers" method
    """

    def setUp(self) -> None:
        """Set up test."""
        super().setUp()
        self.scanner._log_collection = Mock()

    def test_returns_fiber_ifaces(self):
        """
        Tests that list interfaces with fiber glass
        type is saved in "_fibers"
        attribute and returned
        """
        ### Setup ###

        ifaces = [Mock(fiber=True), Mock(fiber=False), Mock(fiber=True)]
        self.scanner._ifaces = Mock(return_value=ifaces)

        ### Run ###

        result = self.scanner.fibers()

        ### Assertions ###

        self.assertEqual([ifaces[0], ifaces[2]], result)
        self.assertEqual([ifaces[0], ifaces[2]], self.scanner._fibers)
        self.scanner._log_collection.assert_called_once_with(name='Fiber Channel Adapters', collection=result)

    def test_returns_stored_fiber_ifaces(self):
        """
        Tests that if originally "_fibers"
        list is not empty, it's returned
        """
        ### Setup ###

        fibers = ['fiber1', 'fiber2']
        self.scanner._fibers = fibers
        self.scanner._ifaces = Mock()

        ### Run ###

        result = self.scanner.fibers()

        ### Assertions ###

        self.assertIs(result, fibers)
        self.assertIs(self.scanner._fibers, fibers)
        self.scanner._ifaces.assert_not_called()
        self.scanner.logger.info.assert_not_called()


class TestLshwExtract(unittest.TestCase):
    """Unit tests for _lshw_extract function."""

    def setUp(self) -> None:
        """Set up test."""
        super(TestLshwExtract, self).setUp()
        self.cpu1 = {'id': '1 cpu', 'class': 'processor', 'claimed': True, 'description': 'Central Process Unit',
                     'physid': '0'}
        self.cpu2 = {'id': '2 cpu', 'class': 'processor', 'claimed': True, 'description': 'Central Process Unit',
                     'physid': '1'}
        output = {
            "id": "thinkpad",
            "class": "system",
            "claimed": True,
            "description": "Computer",
            "width": 64,
            "capabilities": {"smp": "Symmetric Multi-Processing", "vsyscall32": "32-bit processes"},
            "children": [self.cpu1, self.cpu2]
        }
        self.lshw_output = objdict.ObjDict(output)

    def test_extracts_data(self):
        """
        Tests that requested data is extracted
        from "lshw" output and returned
        """
        ### Run ###

        result = list(_lshw_extract(self.lshw_output, cls='processor', id='*cpu'))

        ### Assertions ###

        self.assertEqual([self.cpu1, self.cpu2], result)

    def test_wrong_kwarg(self):
        """
        Tests getting empty result if kwarg is unexpected
        """
        ### Run ###

        result = list(_lshw_extract(self.lshw_output, cls='processor', id='*cpu', wrong_kwarg='value'))

        ### Assertions ###

        self.assertEqual([], result)
