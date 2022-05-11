"""
Unit tests for "controllers.inventory_scanner._ProtoElement" class
"""

import unittest

import objdict

from workers.utils.inventory_scanner import _ProtoElement


class Element(_ProtoElement):
    """Element test class."""

    def __init__(self, data):
        self.field1 = None
        self.field2 = None
        self.field3 = None
        super().__init__(data)

    @property
    def present(self):
        """Present property."""
        return


class TestProtoElement(unittest.TestCase):
    """
    Unit tests for "_ProtoElement" class
    """

    def test_init(self):
        """
        Tests that instance attributes are
        filled with provided data
        """
        ### Setup ###

        data = objdict.ObjDict(Field_1='123', Field_2='456', field3='789')

        ### Run ###

        element = Element(data)

        ### Assertions ###

        self.assertEqual('123', element.field1)
        self.assertEqual('456', element.field2)
        self.assertEqual('789', element.field3)
