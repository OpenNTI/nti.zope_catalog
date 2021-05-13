#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# stdlib imports
import unittest


from hamcrest import assert_that
from hamcrest import is_

from zope.index.topic.filter import PythonFilteredSet

from nti.zope_catalog.topic import ExtentFilteredSet
from nti.zope_catalog.topic import TopicIndex


__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

class Context(object):
    in_extent = False
    in_filter = False
    docid = None

    def __init__(self, in_extent=False, in_filter=False, docid=None):
        self.in_extent = in_extent
        self.in_filter = in_filter
        self.docid = docid

def default_expression(_a, _b, obj):
    return obj.in_extent

class TestTopicIndex(unittest.TestCase):

    def test_apply_mixed_topics(self):
        # We can mix normal filtered sets and extent filtered sets
        # and query appropriately

        extent = ExtentFilteredSet('extent', default_expression)
        _filter = PythonFilteredSet('filter',
                                    'context.in_filter',
                                    family=extent.family)

        index = TopicIndex()
        index.addFilter(extent)
        index.addFilter(_filter)

        in_extent = Context(in_extent=True, docid=1)
        in_filter = Context(in_filter=True, docid=2)
        in_both = Context(in_extent=True, in_filter=True, docid=3)
        in_none = Context(docid=4)

        for x in in_extent, in_filter, in_both, in_none:
            index.index_doc(x.docid, x)

        assert_that(set(index['extent'].getIds()),
                    is_({1, 3}))

        assert_that(set(index['filter'].getIds()),
                    is_({2, 3}))

        assert_that(set(index.apply('extent')),
                    is_({1, 3}))
        assert_that(set(index.apply({'all_of': ['extent']})),
                    is_({1, 3}))
        assert_that(set(index.apply({'any_of': ['extent']})),
                    is_({1, 3}))

        assert_that(set(index.apply('filter')),
                    is_({2, 3}))
        assert_that(set(index.apply({'all_of': ['filter']})),
                    is_({2, 3}))
        assert_that(set(index.apply({'any_of': ['filter']})),
                    is_({2, 3}))

        assert_that(set(index.apply(['extent', 'filter'])),
                    is_({3}))
        assert_that(set(index.apply({'all_of': ['extent', 'filter']})),
                    is_({3}))
        assert_that(set(index.apply({'any_of': ['extent', 'filter']})),
                    is_({1, 2, 3}))

        # Take out in_extent
        in_extent.in_extent = False
        index.index_doc(in_extent.docid, in_extent)

        assert_that(set(index.apply(['extent', 'filter'])),
                    is_({3}))
        assert_that(set(index.apply({'all_of': ['extent', 'filter']})),
                    is_({3}))
        assert_that(set(index.apply({'any_of': ['extent', 'filter']})),
                    is_({2, 3}))

        # take out the one in both
        in_both.in_extent = False
        index.index_doc(in_both.docid, in_both)

        assert_that(set(index.apply(['extent', 'filter'])),
                    is_(set()))
        assert_that(set(index.apply({'all_of': ['extent', 'filter']})),
                    is_(set()))
        assert_that(set(index.apply({'any_of': ['extent', 'filter']})),
                    is_({2, 3}))


class TestExtentFilteredSet(unittest.TestCase):

    def test_ids_and_extent(self):
        extent = ExtentFilteredSet('extent', default_expression)
        assert_that(extent.ids(), is_(()))

        in_extent = Context(in_extent=True, docid=1)
        in_none = Context(docid=4)

        extent.index_doc(in_extent.docid, in_extent)
        extent.index_doc(in_none.docid, in_none)

        assert_that(extent.ids(), is_((1,)))
        extent_extent = extent.getExtent()
        assert_that(list(extent_extent.set),
                    is_([1]))

    def test_index_doc_doesnt_unindex_on_ValueError(self):
        extent = ExtentFilteredSet('extent', default_expression)
        in_none = Context(docid=4)
        extent.unindex_doc = lambda *args: self.fail("Should not call")
        extent.index_doc(in_none.docid, in_none)

        assert_that(extent.ids(), is_(()))

    def test_index_doc_doesnt_unindex_on_ValueError_with_jar(self):
        extent = ExtentFilteredSet('extent', default_expression)


        in_extent = Context(in_extent=True, docid=1)
        in_none = Context(docid=4)
        # The Python implementation of BTrees always calls readCurrent, but
        # the C implementation doesn't do it if its empty.
        extent.index_doc(in_extent.docid, in_extent)

        # Now break the jar
        class MockJar(object):
            def readCurrent(self, _):
                raise AssertionError("Should not call") # pragma: no cover

        extent._ids._p_jar = MockJar()
        extent._ids._p_oid = b'12345678'
        extent._extent._p_jar = MockJar()
        extent._extent._p_oid = b'12345678'

        extent.index_doc(in_none.docid, in_none)

        assert_that(extent.ids(), is_((1,)))
