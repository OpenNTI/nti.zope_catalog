#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import is_not
from hamcrest import raises
from hamcrest import calling
from hamcrest import has_key
from hamcrest import contains
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property
from hamcrest import none

import unittest

import BTrees

from zope import interface

from nti.zope_catalog.interfaces import INoAutoIndex
from nti.zope_catalog.catalog import Catalog
from nti.zope_catalog.catalog import ResultSet
from . import NTIZopeCatalogLayer

family = BTrees.family64

class Content(object):
    pass

@interface.implementer(INoAutoIndex)
class NoIndexContent(object):
    pass

class MockCatalog(Catalog):
    def _visitAllSublocations(self):
        yield 1, Content()
        yield 2, NoIndexContent()


class TestCatalog(unittest.TestCase):

    def test_visit_sublocations(self):
        cat = MockCatalog()
        locs = list(cat._visitSublocations())
        assert_that(locs, has_length(1))
        assert_that(locs[0],
                    contains(1, is_(Content)))

    def test_update_indexes_with_error(self):
        from zope.testing.loggingsupport import InstalledHandler
        handler = InstalledHandler('nti.zope_catalog.catalog')
        self.addCleanup(handler.uninstall)

        cat = MockCatalog()
        cat._PERSISTENCE_EXCEPTIONS = AttributeError

        cat['key'] = 42

        cat.updateIndexes(ignore_persistence_exceptions=True)

        assert_that(handler.records, has_length(1))
        assert_that(handler.records[0].msg,
                    is_("Error indexing object %s(%s); %s"))

    def test_update_index_with_error(self):
        from zope.testing.loggingsupport import InstalledHandler
        handler = InstalledHandler('nti.zope_catalog.catalog')
        self.addCleanup(handler.uninstall)

        cat = MockCatalog()
        cat._PERSISTENCE_EXCEPTIONS = AttributeError

        cat.updateIndex(42, ignore_persistence_exceptions=True)

        assert_that(handler.records, has_length(1))
        assert_that(handler.records[0].msg,
                    is_("Error indexing object %s(%s); %s"))

    def test_visit_sublocations_non_configured(self):
        cat = Catalog()
        cat._visitAllSublocations()

class TestResultSet(unittest.TestCase):

    def test_len(self):
        r = ResultSet((1,), None)
        assert_that(r, has_length(1))

    def test_iter(self):
        class UIDS(object):
            def getObject(self, uid):
                return self

        uids = UIDS()
        r = ResultSet((1,), uids)
        assert_that(list(r), is_([uids]))
        assert_that(r, has_length(1))
        assert_that(r.count(), is_(1))

    def test_broken(self):
        # The functionality itself is broken.
        import warnings
        class UIDS(object):
            def queryObject(self, uid):
                return None

        with warnings.catch_warnings(record=True) as w:
            r = ResultSet((1,), UIDS(), True)

        x = r.get_object(1)
        assert_that(x, is_(none()))

        assert_that(w, has_length(1))

class TestConfigure(unittest.TestCase):

    layer = NTIZopeCatalogLayer

    def test_noop(self):
        # We just exist to make sure the configure could be loaded.
        # We don't actually verify anything it does...because it
        # does nothing
        return
