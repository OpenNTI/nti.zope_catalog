#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import assert_that

import unittest

from zope import interface

from zope.interface import Interface
from zope.interface import directlyProvides

from zope.location.interfaces import ILocation

from nti.zope_catalog.location import lineage
from nti.zope_catalog.location import find_interface

from nti.zope_catalog.tests import SharedConfiguringTestLayer


@interface.implementer(ILocation)
class Location(object):
    __name__ = __parent__ = None


class TestLineage(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def _callFUT(self, context):
        return lineage(context)

    def test_lineage(self):
        o1 = Location()
        o2 = Location()
        o2.__parent__ = o1
        o3 = Location()
        o3.__parent__ = o2
        o4 = Location()
        o4.__parent__ = o3
        result = list(self._callFUT(o3))
        assert_that(result, is_([o3, o2, o1]))
        result = list(self._callFUT(o1))
        assert_that(result, is_([o1]))


class DummyContext(object):

    __parent__ = None

    def __init__(self, next_=None, name=None):
        self.next = next_
        self.__name__ = name

    def __getitem__(self, name):
        if self.next is None:
            raise KeyError(name)
        return self.next

    def __repr__(self):
        return '<DummyContext with name %s at id %s>' % (self.__name__, id(self))


class TestFindInterface(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def _callFUT(self, context, iface):
        return find_interface(context, iface)

    def test_it_interface(self):
        baz = DummyContext()
        bar = DummyContext(baz)
        foo = DummyContext(bar)
        root = DummyContext(foo)
        root.__parent__ = None
        root.__name__ = 'root'
        foo.__parent__ = root
        foo.__name__ = 'foo'
        bar.__parent__ = foo
        bar.__name__ = 'bar'
        baz.__parent__ = bar
        baz.__name__ = 'baz'

        class IFoo(Interface):
            pass
        directlyProvides(root, IFoo)
        result = self._callFUT(baz, IFoo)
        self.assertEqual(result.__name__, 'root')
