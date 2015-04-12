#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import raises
from hamcrest import calling
from hamcrest import has_key
from hamcrest import contains
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property

import unittest

import BTrees

from nti.zope_catalog.index import IntegerAttributeIndex
from nti.zope_catalog.index import NormalizingKeywordIndex
from nti.zope_catalog.index import CaseInsensitiveAttributeFieldIndex

family = BTrees.family64

class TestNormalizingKeywordIndex(unittest.TestCase):

	field = 'VALUE'

	def setUp(self):
		super(TestNormalizingKeywordIndex,self).setUp()
		self.index = NormalizingKeywordIndex()

	def test_family(self):
		assert_that( self.index, has_property('family', family) )

	def test_ids(self):
		self.index.index_doc( 1, ('aizen',))
		self.index.index_doc( 2, ['ichigo'])
		self.index.index_doc( 3, ['Kuchiki', 'rukia'])
		ids = sorted(list(self.index.ids()))
		assert_that(ids, is_([1,2,3]))
		
	def test_remove_words(self):
		self.index.index_doc( 1, ('aizen',))
		self.index.index_doc( 2, ['ichigo'])
		self.index.index_doc( 3, ['Kuchiki', 'rukia'])
		assert_that(self.index.documentCount(), is_(3))
		assert_that(self.index.wordCount(), is_(4))
		
		self.index.remove_words(['xxx'])
		ids = sorted(list(self.index.ids()))
		assert_that(ids, is_([1,2,3]))
		assert_that(self.index.documentCount(), is_(3))
		assert_that(self.index.wordCount(), is_(4))
		
		self.index.remove_words(('aizen',))
		ids = sorted(list(self.index.ids()))
		assert_that(ids, is_([2,3]))
		assert_that(self.index.documentCount(), is_(2))
		assert_that(self.index.wordCount(), is_(3))
		
		self.index.remove_words(('rukia',))
		ids = sorted(list(self.index.ids()))
		assert_that(ids, is_([2,3]))
		assert_that(self.index.documentCount(), is_(2))
		assert_that(self.index.wordCount(), is_(2))
		
		self.index.remove_words(('Kuchiki',))
		ids = sorted(list(self.index.ids()))
		assert_that(ids, is_([2]))
		assert_that(self.index.documentCount(), is_(1))
		assert_that(self.index.wordCount(), is_(1))

	def test_apply(self):
		self.index.index_doc( 1, ('aizen',))
		self.index.index_doc( 2, ['ichigo'])
		self.index.index_doc( 3, ['Kuchiki'])
		self.index.index_doc( 4, ['renji', 'zaraki'])
		
		res = self.index.apply({'query':['ichigo']})
		assert_that(res, has_length(1))
		assert_that(res, contains(2))
		
		res = self.index.apply({'query':'kuchiki'})
		assert_that(res, has_length(1))
		assert_that(res, contains(3))
		
		res = self.index.apply({'query':['aizen','kuchiki'], 'operator':'or'})
		assert_that(res, has_length(2))
		
		res = self.index.apply({'query':['aizen','kuchiki'], 'operator':'and'})
		assert_that(res, has_length(0))
		
		res = self.index.apply('aizen')
		assert_that(res, has_length(1))
		assert_that(res, contains(1))
		
		res = self.index.apply({'any_of': ('aizen','kuchiki')})
		assert_that(res, has_length(2))
		
		res = self.index.apply({'any': None})
		assert_that(res, has_length(4))
		
		res = self.index.apply({'all': ('aizen','ichigo')})
		assert_that(res, has_length(0))
		
		res = self.index.apply({'all': ('zaraki','renji')})
		assert_that(res, has_length(1))
		
		res = self.index.apply({'between': ('a','z')})
		assert_that(res, has_length(4))
				
		res = self.index.apply({'between': ('r','z')})
		assert_that(res, has_length(1))
		
		res = self.index.apply(['rukia'])
		assert_that(res, has_length(0))
		
		res = self.index.apply([1,2,3])
		assert_that(res, has_length(0))
		
class TestCaseInsensitiveAttributeIndex(unittest.TestCase):

	field = 'VALUE'

	def setUp(self):
		super(TestCaseInsensitiveAttributeIndex,self).setUp()
		self.index = CaseInsensitiveAttributeFieldIndex('field')

	def test_family(self):
		assert_that( self.index, has_property('family', family) )

	def test_noramlize_on_index(self):
		self.index.index_doc( 1, self)
		assert_that( self.index._fwd_index, has_key('value'))

class TestIntegerAttributeIndex(unittest.TestCase):

	field = 1234

	def setUp(self):
		super(TestIntegerAttributeIndex,self).setUp()
		self.index = IntegerAttributeIndex('field')

	def test_family(self):
		assert_that( self.index, has_property('family', family) )
		assert_that( self.index, has_property('_rev_index',
											  is_(family.II.BTree)))
		assert_that( self.index, has_property('_fwd_index',
											  is_(family.IO.BTree)))

	def test_index_wrong_value(self):
		self.field = 'str'

		assert_that( calling(self.index.index_doc).with_args(1, self),
					 raises(TypeError))

	def test_query(self):
		index = self.index
		index.index_doc( 1, self )

		# BWC code
		# exact match
		assert_that( index.apply( (self.field, self.field)),
					 contains( 1 ))
		# range
		assert_that( index.apply( (1, 2048)),
					 contains( 1 ) )

	def test_index_sort(self):
		index = self.index
		self.field = 1
		index.index_doc( 1, self )
		self.field = 2
		index.index_doc( 2, self )
		self.field = 3
		index.index_doc( 3, self )

		assert_that( index.sort((1,2,3), reverse=True),
					 contains(3, 2, 1))

		assert_that( index.sort((3, 2, 1), reverse=False),
					 contains(1, 2, 3))
