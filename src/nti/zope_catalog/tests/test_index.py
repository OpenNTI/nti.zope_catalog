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

from nti.zope_catalog.index import stemmer_lexicon

from nti.zope_catalog.index import AttributeTextIndex
from nti.zope_catalog.index import IntegerAttributeIndex
from nti.zope_catalog.index import NormalizingFieldIndex
from nti.zope_catalog.index import NormalizingKeywordIndex
from nti.zope_catalog.index import CaseInsensitiveAttributeFieldIndex
from nti.zope_catalog.index import ValueIndex
from nti.zope_catalog.index import SetIndex
from nti.zope_catalog.index import IntegerValueIndex

family = BTrees.family64

class TestNormalizingFieldIndex(unittest.TestCase):

    def setUp(self):
        super(TestNormalizingFieldIndex, self).setUp()
        class _NormalizingIndex(NormalizingFieldIndex):
            def normalize(self, value):
                return value.lower() if value else value
        self.index = _NormalizingIndex()

    def test_ids(self):
        assert_that(list(self.index.ids()),
                    is_([]))

        self.index.index_doc(1, 'FOO')
        assert_that(list(self.index.ids()),
                    is_([1]))

    def test_doc_value(self):
        assert_that(self.index.doc_value(1),
                    is_(none()))
        self.index.index_doc(1, 'FOO')
        assert_that(self.index.doc_value(1),
                    is_('foo'))

    def test_apply(self):
        assert_that(list(self.index.apply(('FOO', 'FOO'))),
                    is_([]))
        self.index.index_doc(1, 'FOO')
        assert_that(list(self.index.apply(('foo', 'foo'))),
                    is_([1]))

    def test_zip(self):
        assert_that(list(self.index.zip((1,))),
                    is_([(1, None)]))
        self.index.index_doc(1, 'FOO')
        assert_that(list(self.index.zip((1,))),
                    is_([(1, 'foo')]))

class TestValueIndex(unittest.TestCase):

    def setUp(self):
        super(TestValueIndex, self).setUp()
        self.index = ValueIndex()

    def test_zip(self):
        assert_that(list(self.index.zip((1,))),
                    is_([(1, None)]))
        self.index.index_doc(1, 'FOO')
        assert_that(list(self.index.zip((1,))),
                    is_([(1, 'FOO')]))

class TestSetIndex(unittest.TestCase):

    def setUp(self):
        super(TestSetIndex, self).setUp()
        self.index = SetIndex()

    def test_zip(self):
        assert_that(list(self.index.zip((1,))),
                    is_([(1, None)]))
        self.index.index_doc(1, ['FOO'])
        assert_that(list(self.index.zip((1,))),
                    is_([(1, {'FOO'})]))

class TestIntegerValueIndex(unittest.TestCase):

    def setUp(self):
        super(TestIntegerValueIndex, self).setUp()
        self.index = IntegerValueIndex()

    def test_zip(self):
        assert_that(list(self.index.zip((1,))),
                    is_([(1, None)]))
        self.index.index_doc(1, 1)
        assert_that(list(self.index.zip((1,))),
                    is_([(1, 1)]))

class TestNormalizingKeywordIndex(unittest.TestCase):

    field = 'VALUE'

    def setUp(self):
        super(TestNormalizingKeywordIndex, self).setUp()
        self.index = NormalizingKeywordIndex()

    def test_family(self):
        assert_that(self.index, has_property('family', family))

    def test_zip(self):
        assert_that(list(self.index.zip((1,))),
                    is_([(1, None)]))
        self.index.index_doc(1, ['Foo'])
        assert_that(list(self.index.zip((1,))),
                    is_([(1, {'foo'})]))

    def test_ids_and_words(self):
        self.index.index_doc(1, ('aizen',))
        self.index.index_doc(2, ['ichigo'])
        self.index.index_doc(3, ['Kuchiki', 'rukia'])
        ids = sorted(self.index.ids())
        assert_that(ids, is_([1, 2, 3]))

        words = sorted(self.index.words())
        assert_that(words,
                    is_(['aizen', 'ichigo', 'kuchiki', 'rukia']))

    def test_remove_words(self):
        index = self.index
        index.index_doc(1, ('aizen',))
        index.index_doc(2, ['ichigo'])
        index.index_doc(3, ['Kuchiki', 'rukia'])
        assert_that(index.documentCount(), is_(3))
        assert_that(index.wordCount(), is_(4))

        index.remove_words(['xxx'])
        ids = sorted(list(index.ids()))
        assert_that(ids, is_([1, 2, 3]))
        assert_that(index.documentCount(), is_(3))
        assert_that(index.wordCount(), is_(4))

        index.remove_words(('aizen',))
        ids = sorted(list(index.ids()))
        assert_that(ids, is_([2, 3]))
        assert_that(index.documentCount(), is_(2))
        assert_that(index.wordCount(), is_(3))

        index.remove_words(('rukia',))
        ids = sorted(list(index.ids()))
        assert_that(ids, is_([2, 3]))
        assert_that(index.documentCount(), is_(2))
        assert_that(index.wordCount(), is_(2))

        index.remove_words(('Kuchiki',))
        ids = sorted(list(index.ids()))
        assert_that(ids, is_([2]))
        assert_that(index.documentCount(), is_(1))
        assert_that(index.wordCount(), is_(1))

    def test_remove_words_in_already_corrupted_index(self):
        from zope.testing.loggingsupport import InstalledHandler
        handler = InstalledHandler('nti.zope_catalog.index')
        self.addCleanup(handler.uninstall)

        index = self.index
        index.index_doc(1, ('aizen',))
        index.index_doc(2, ['ichigo'])
        index.index_doc(3, ['Kuchiki', 'rukia'])
        del index._rev_index[3]
        index.remove_words(('Kuchiki',))
        assert_that(handler.records[0].msg, is_("Your index is corrupted: %s"))


    def test_apply(self):
        index = self.index
        index.index_doc(1, ('aizen',))
        index.index_doc(2, ['ichigo'])
        index.index_doc(3, ['Kuchiki'])
        index.index_doc(4, ['renji', 'zaraki'])

        # Bad queries first
        assert_that(list(index.apply({})),
                    is_([]))
        assert_that(calling(index.apply).with_args({'a': 1, 'b': 2}),
                    raises(ValueError))
        assert_that(calling(index.apply).with_args(self),
                    raises(ValueError))

        res = index.apply({'query': ['ichigo']})
        assert_that(res, has_length(1))
        assert_that(res, contains(2))

        res = index.apply({'query': 'kuchiki'})
        assert_that(res, has_length(1))
        assert_that(res, contains(3))

        res = index.apply({'query': ['aizen', 'kuchiki'],
                                 'operator': 'or'})
        assert_that(res, has_length(2))

        res = index.apply({'query': ['aizen', 'kuchiki'],
                                 'operator': 'and'})
        assert_that(res, has_length(0))

        res = index.apply('aizen')
        assert_that(res, has_length(1))
        assert_that(res, contains(1))

        res = index.apply({'any_of': ('aizen', 'kuchiki')})
        assert_that(res, has_length(2))

        res = index.apply({'any': None})
        assert_that(res, has_length(4))

        res = index.apply({'all': ('aizen', 'ichigo')})
        assert_that(res, has_length(0))

        res = index.apply({'all': ('zaraki', 'renji')})
        assert_that(res, has_length(1))

        res = index.apply({'between': ('a', 'z')})
        assert_that(res, has_length(4))

        res = index.apply({'between': ('r', 'z')})
        assert_that(res, has_length(1))

        res = index.apply(['rukia'])
        assert_that(res, has_length(0))

        res = index.apply([1, 2, 3])
        assert_that(res, has_length(0))

        # Extent query
        from zc.catalog.extentcatalog import Extent
        extent = Extent(family)
        assert_that(list(index.apply(extent)),
                    is_([]))
        extent.add(1, None)

        assert_that(list(index.apply(extent)),
                    is_([1]))

        assert_that(list(index.apply({'any': extent})),
                    is_([1]))


class TestCaseInsensitiveAttributeIndex(unittest.TestCase):

    field = 'VALUE'

    def setUp(self):
        super(TestCaseInsensitiveAttributeIndex, self).setUp()
        self.index = CaseInsensitiveAttributeFieldIndex('field')

    def test_family(self):
        assert_that(self.index, has_property('family', family))

    def test_noramlize_on_index(self):
        self.index.index_doc(1, self)
        assert_that(self.index._fwd_index, has_key('value'))


class TestIntegerAttributeIndex(unittest.TestCase):

    field = 1234

    def setUp(self):
        super(TestIntegerAttributeIndex, self).setUp()
        self.index = IntegerAttributeIndex('field')

    def test_family(self):
        assert_that(self.index, has_property('family', family))
        assert_that(self.index, has_property('_rev_index',
                                             is_(family.II.BTree)))
        assert_that(self.index, has_property('_fwd_index',
                                             is_(family.IO.BTree)))

    def test_index_wrong_value(self):
        self.field = 'str'

        assert_that(calling(self.index.index_doc).with_args(1, self),
                    raises(TypeError))

    def test_query(self):
        index = self.index
        index.index_doc(1, self)

        # BWC code
        # exact match
        assert_that(index.apply((self.field, self.field)),
                    contains(1))
        # range
        assert_that(index.apply((1, 2048)),
                    contains(1))

    def test_index_sort(self):
        index = self.index
        self.field = 1
        index.index_doc(1, self)
        self.field = 2
        index.index_doc(2, self)
        self.field = 3
        index.index_doc(3, self)

        assert_that(index.sort((1, 2, 3), reverse=True),
                    contains(3, 2, 1))

        assert_that(index.sort((3, 2, 1), reverse=False),
                    contains(1, 2, 3))


class TestAttributeTextIndex(unittest.TestCase):

    field = u'Humans are valuable resources and the more we have of them the better'

    def test_query_stemmer(self):
        index = AttributeTextIndex('field',
                                   lexicon=stemmer_lexicon())
        index.index_doc(1, self)

        assert_that(index.documentCount(), is_(1))

        # Make sure the words got stemmed correctly. This fails
        # if zopyx.txng3.ext is not installed.
        assert_that(index.lexicon.get_wid('resources'), is_(0))
        assert_that(index.lexicon.get_wid('resource'), is_(0))
        assert_that(index.lexicon.get_wid('resourc'), is_not(0))



        assert_that(index.apply("resource"),
                    contains(1))

        assert_that(index.apply("human"),
                    contains(1))

        assert_that(index.apply("valuable"),
                    contains(1))

        assert_that(list(index.apply("resource*")),
                    is_([]))
