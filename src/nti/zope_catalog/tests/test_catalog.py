#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# stdlib imports
import unittest

from hamcrest import assert_that
from hamcrest import contains_exactly as contains
from hamcrest import is_not as does_not
from hamcrest import has_length
from hamcrest import is_
from hamcrest import none


import BTrees
from zope import interface
from zope.annotation.interfaces import IAttributeAnnotatable
from zope.catalog.interfaces import ICatalog

from zope.index.interfaces import IIndexSearch
from zope.container.interfaces import IBTreeContainer
from zope.location.interfaces import ILocation
from persistent.interfaces import IPersistent
from persistent import Persistent

from nti.testing.matchers import validly_provides
from nti.testing.matchers import verifiably_provides
from nti.testing.matchers import implements
from nti.zope_catalog.catalog import Catalog
from nti.zope_catalog.catalog import DeferredCatalog
from nti.zope_catalog.catalog import ResultSet
from nti.zope_catalog.interfaces import IDeferredCatalog
from nti.zope_catalog.interfaces import INoAutoIndex


from . import NTIZopeCatalogLayer


__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904


family = BTrees.family64

class Content(object):
    pass

@interface.implementer(INoAutoIndex)
class NoIndexContent(Persistent):
    pass

class PersistentContent(Persistent):
    pass

class MockCatalog(Catalog):

    def __init__(self):
        super(MockCatalog, self).__init__()
        self.mock_catalog_data = [
            (1, Content()),
            (2, NoIndexContent())
        ]

    def _visitAllSublocations(self):
        for thing in self.mock_catalog_data:
            yield thing


class IDNE(interface.Interface): # pylint:disable=inherit-non-class
    "Not implemented by anything"

class TestCatalog(unittest.TestCase):

    main_interface = ICatalog
    extra_interfaces = (IAttributeAnnotatable, IIndexSearch,
                        IBTreeContainer, ILocation,
                        IPersistent)
    doesnt_provide_interfaces = (IDNE,)

    def _makeOne(self):
        return Catalog()

    def test_visit_sublocations_non_configured(self):
        cat = self._makeOne()
        cat._visitAllSublocations()

    def test_provides(self):
        cat = self._makeOne()
        assert_that(type(cat), implements(self.main_interface))
        assert_that(cat, validly_provides(self.main_interface))
        assert_that(cat, validly_provides(*self.extra_interfaces))
        assert_that(cat, does_not(verifiably_provides(*self.doesnt_provide_interfaces)))

class TestDeferredCatalog(TestCatalog):

    main_interface = IDeferredCatalog
    doesnt_provide_interfaces = (ICatalog,)


    def _makeOne(self):
        return DeferredCatalog()

class TestCatalogFull(TestCatalog):

    def _makeOne(self):
        return MockCatalog()

    def test_visit_sublocations(self):
        cat = self._makeOne()
        locs = list(cat._visitSublocations())
        assert_that(locs, has_length(1))
        assert_that(locs[0],
                    contains(1, is_(Content)))

    def test_visit_sublocations_check_class_only(self):
        from zope.interface import alsoProvides
        class MyException(Exception):
            pass

        @interface.implementer(INoAutoIndex)
        class NoIndex(object):
            # Deliberately break testing providedBy on instances.
            # This also proves that we don't unnecessarily activate
            # persistent objects, because they hook in at ``__getattribute__``
            def __getattribute__(self, name):
                raise MyException

        noindex = NoIndex()
        with self.assertRaises(MyException):
            INoAutoIndex.providedBy(noindex)

        cat = self._makeOne()
        cat.mock_catalog_data.append((3, noindex))
        content = PersistentContent()
        alsoProvides(content, INoAutoIndex)
        cat.mock_catalog_data.append((4, content))

        locs = list(cat._visitSublocations())
        assert_that(locs, has_length(1))
        assert_that(locs[0],
                    contains(1, is_(Content)))

    def test_visit_sublocations_check_class_only_not_activate(self):
        from ZODB.DB import DB
        from ZODB.DemoStorage import DemoStorage
        import transaction
        from zope.interface import alsoProvides

        cat = self._makeOne()
        content = PersistentContent()
        alsoProvides(content, INoAutoIndex)
        cat.mock_catalog_data.append((4, content))

        db = DB(DemoStorage())
        self.addCleanup(db.close)
        transaction.begin()
        conn = db.open()
        self.addCleanup(conn.close)
        conn.root.cat = cat
        transaction.commit()

        transaction.begin()
        conn.cacheMinimize()
        assert_that(conn.root.cat.mock_catalog_data[1][1], is_(NoIndexContent))
        assert_that(conn.root.cat.mock_catalog_data[1][1]._p_status, is_('ghost'))
        assert_that(conn.root.cat.mock_catalog_data[-1][1], is_(PersistentContent))
        assert_that(conn.root.cat.mock_catalog_data[-1][1]._p_status, is_('ghost'))

        locs = list(cat._visitSublocations())
        assert_that(locs, has_length(1))
        assert_that(locs[0],
                    contains(1, is_(Content)))
        # Still a ghost
        assert_that(conn.root.cat.mock_catalog_data[1][1]._p_status, is_('ghost'))
        # But the one that alsoProvides() had to wake up
        assert_that(conn.root.cat.mock_catalog_data[-1][1]._p_status, is_('saved'))

    def test_update_indexes_with_error(self):
        from zope.testing.loggingsupport import InstalledHandler
        handler = InstalledHandler('nti.zope_catalog.catalog')
        self.addCleanup(handler.uninstall)

        cat = self._makeOne()
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

        cat = self._makeOne()
        cat._PERSISTENCE_EXCEPTIONS = AttributeError

        cat.updateIndex(42, ignore_persistence_exceptions=True)

        assert_that(handler.records, has_length(1))
        assert_that(handler.records[0].msg,
                    is_("Error indexing object %s(%s); %s"))


class TestResultSet(unittest.TestCase):

    def test_len(self):
        r = ResultSet((1,), None)
        assert_that(r, has_length(1))

    def test_iter(self):
        class UIDS(object):
            def getObject(self, uid):
                return self

        uids = UIDS()
        r = ResultSet((1, 2, 3), uids)
        assert_that(list(r), is_([uids, uids, uids]))
        assert_that(r, has_length(3))
        assert_that(r.count(), is_(3))

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


class TestCatalogPrefetchIterator(unittest.TestCase):

    def _makeOne(self, iterable, chunk_size):
        from ..catalog import CatalogPrefetchIterator
        return CatalogPrefetchIterator(iterable, chunk_size)

    class Jar(object):
        prefetched = ()

        databases = ()

        def db(self):
            return self

        def prefetch(self, oids):
            self.prefetched += (oids,)

    class Obj(object):
        def __init__(self, jar=None, oid=None):
            self._p_jar = jar
            self._p_oid = oid

    def test_prefetch_singledb(self):
        jar = self.Jar()
        inst = self._makeOne([], 0)

        chunk = [
            (1, self.Obj()),
            (2, self),
            (3, object()),
            (4, Persistent()),
            (5, self.Obj(jar, 1)),
            (5, self.Obj(jar, 2)),
            (5, self.Obj(jar, 3)),
        ]

        inst._prefetch(chunk)

        assert_that(jar.prefetched, is_(({1, 2, 3},)))
        assert_that(inst._prefetch, is_(inst._prefetch_singledb))

    def test_prefetch_multidb(self):
        jar1 = self.Jar()
        jar2 = self.Jar()
        jar3 = self.Jar()
        databases = {'1': jar1, '2': jar2, '3': jar3}
        jar1.databases = jar2.databases = jar3.databases = databases
        inst = self._makeOne([], 0)

        chunk = [
            (1, self.Obj(jar3)),
            (2, self),
            (3, object()),
            (4, Persistent()),
            (5, self.Obj(jar1, 1)),
            (5, self.Obj(jar2, 2)),
            (5, self.Obj(jar3, 3)),
            (5, self.Obj(jar3, 4)),
            (5, self.Obj(jar2, 5)),
            (5, self.Obj(jar3, 5)), # dup, different jar
            (5, self.Obj(jar3, 5)), # dup, same jar
        ]

        inst._prefetch(chunk)

        assert_that(inst._prefetch, is_(inst._prefetch_multidb))
        assert_that(jar1.prefetched, is_(({1,},)))
        assert_that(jar2.prefetched, is_(({2, 5},)))
        assert_that(jar3.prefetched, is_(({3, 4, 5},)))
