#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Support for working with :class:`zope.catalog.field` indexes.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import collections

from zope import interface

from zope.catalog.field import IFieldIndex
from zope.catalog.attribute import AttributeIndex
from zope.catalog.interfaces import ICatalogIndex

import zope.index.field
import zope.index.keyword
import zope.container.contained

import zc.catalog.index
import zc.catalog.catalogindex

import BTrees

from nti.common.property import alias
from nti.common.iterables import is_nonstr_iter

from .interfaces import IKeywordIndex

def convertQuery(query):
	# Convert zope.index style two-tuple (min/max)
	# query to new-style
	if isinstance(query, tuple) and len(query) == 2:
		if query[0] == query[1]:
			# common case of exact match
			query = {'any_of': (query[0],)}
		else:
			query = {'between': query}
	return query

class _ZCApplyMixin(object):
	"""
	Convert zope.index style two-tuple query to new style.
	"""

	def apply(self, query):
		query = convertQuery(query)
		return super(_ZCApplyMixin,self).apply(query)

class _ZCAbstractIndexMixin(object):
	"""
	Helpers and compatibility mixins for zope.catalog and zc.catalog.
	Makes zc.catalog indexes look a bit more like zope.catalog indexes.
	"""

	family = BTrees.family64
	_num_docs = alias('documentCount')
	_fwd_index = alias('values_to_documents')
	_rev_index = alias('documents_to_values')

@interface.implementer(IFieldIndex)
class NormalizingFieldIndex(zope.index.field.FieldIndex,
							zope.container.contained.Contained):
	"""
	A field index that normalizes before indexing or searching.

	.. note:: For more flexibility, use a :class:`NormalizationWrapper`.
	"""

	#: We default to 64-bit trees
	family = BTrees.family64

	def normalize( self, value ):
		raise NotImplementedError()

	def index_doc(self, docid, value):
		super(NormalizingFieldIndex,self).index_doc( docid, self.normalize(value) )

	def apply( self, query ):
		return super(NormalizingFieldIndex,self).apply( tuple([self.normalize(x) for x in query]) )

class CaseInsensitiveAttributeFieldIndex(AttributeIndex,
										 NormalizingFieldIndex):
	"""
	An attribute index that normalizes case. It is queried with a two-tuple giving the
	min and max values.
	"""

	def normalize( self, value ):
		if value:
			value = value.lower()
		return value

# Normalizing and wrappers:
# The normalizing code needs to get the actual values. Because AttributeIndex
# gets the attribute value in index_doc and then calls the same method on super
# with that returned value, the NormalizationWrapper has to extend AttributeIndex
# to get the right value to pass to the normamlizer. That means it cannot be used
# to wrap another AttributeIndex, only a plain ValueIndex or SetIndex. Note
# that it is somewhat painful to construct

class ValueIndex(_ZCApplyMixin,
				 _ZCAbstractIndexMixin,
				 zc.catalog.index.ValueIndex):
	pass

class AttributeValueIndex(ValueIndex,
						  zc.catalog.catalogindex.ValueIndex):
	pass

class SetIndex(_ZCAbstractIndexMixin,
			   zc.catalog.index.SetIndex):
	pass

class AttributeSetIndex(SetIndex,
						zc.catalog.catalogindex.SetIndex):
	pass

class IntegerValueIndex(_ZCApplyMixin,
						_ZCAbstractIndexMixin,
						zc.catalog.index.ValueIndex):
	"""
	A \"raw\" index that is optimized for, and only supports,
	storing integer values. To normalize, use a :class:`zc.catalog.index.NormalizationWrapper`;
	to store in a catalog and normalize, use a  :class:`NormalizationWrapper`
	(which is an attribute index).
	"""
	def clear(self):
		super(IntegerValueIndex, self).clear()
		self.documents_to_values = self.family.II.BTree()
		self.values_to_documents = self.family.IO.BTree()

class IntegerAttributeIndex(IntegerValueIndex,
							zc.catalog.catalogindex.ValueIndex):
	"""
	An attribute index that is optimized for, and only supports,
	storing integer values. To normalize, use a :class:`zc.catalog.index.NormalizationWrapper`;
	note that because :class:`zc.catalog.catalogindex.NormalizationWrapper` is
	also an attribute index it cannot be used to wrap this class, and your normalizer
	will have to return an object that has the right attribute.
	"""

@interface.implementer(IKeywordIndex)
class NormalizingKeywordIndex(zope.index.keyword.CaseInsensitiveKeywordIndex,
							  zope.container.contained.Contained):
	
	family = BTrees.family64

	def _parseQuery(self, query):
		if isinstance(query, collections.Mapping):
			if 'query' in query: # support legacy 
				query_type = query.get('operator') or 'and'
				query = query['query']
			elif len(query) > 1:
				raise ValueError('may only pass one of key, value pair')
			elif not query:
				return None, None
			else:
				query_type, query = query.items()[0]
				query_type = query_type.lower()
		elif isinstance(query, six.string_types):
			query_type = 'and'
		elif is_nonstr_iter(query):
			query_type = 'and'
		elif zc.catalog.interfaces.IExtent.providedBy(query):
			query_type = 'none'
		else:
			raise ValueError('Invalid query')
		
		if query_type not in ('any', 'none'):
			query = list(query) if is_nonstr_iter(query) else [query]
			query = [x for x in query if isinstance(x, six.string_types)]
			if not query:
				query_type, query =  None, None	
			elif query_type == 'any_of':
				query_type = 'or'	
			elif query_type == 'all':
				query_type = 'and'
		return query_type, query
	
	def apply(self, query): # any_of, any, between, none,
		query = convertQuery(query)
		query_type, query = self._parseQuery(query)
		if query_type is None:
			res = self.family.IF.Set()
		elif query_type in ('or', 'and'):
			res = super(NormalizingKeywordIndex,self).search(query, operator=query_type)
		elif query_type in ('between'):
			query = list(self._fwd_index.iterkeys(query[0], query[1]))
			res = super(NormalizingKeywordIndex,self).search(query, operator='or')
		elif query_type == 'none':
			assert zc.catalog.interfaces.IExtent.providedBy(query)
			res = query - self.family.IF.Set(self.ids())
		elif query_type == 'any':
			if query is None:
				res = self.family.IF.Set(self.ids())
			else:
				assert zc.catalog.interfaces.IExtent.providedBy(query)
				res = query & self.family.IF.Set(self.ids())
		else:
			raise ValueError("unknown query type", query_type)
		return res
	
	def ids(self):
		return self._rev_index.keys()
	
	def words(self):
		return self._fwd_index.keys()
	
	def remove_words(self, *seq):
		seq = self.normalize(*seq)
		for word in seq:
			try:
				docids = self._fwd_index[word]
				del self._fwd_index[word]
				for docid in docids:
					try:
						s = self._rev_index[docid]
						s.remove(word)
						if not s:
							del self._rev_index[docid]
							self._num_docs.change(-1)
					except KeyError:
						pass
			except KeyError:
				pass
	removeWords = remove_words

class AttributeKeywordIndex(AttributeIndex, NormalizingKeywordIndex):
	pass

@interface.implementer(ICatalogIndex) # The superclass forgets this
class NormalizationWrapper(_ZCApplyMixin,
						   zc.catalog.catalogindex.NormalizationWrapper):
	"""
	An attribute index that wraps a raw index and normalizes values.

	This class exists mainly to sort out the difficulty constructing
	instances by only accepting keyword arguments.
	"""

	def __init__( self, field_name=None, interface=None, field_callable=False,
				  index=None, normalizer=None, is_collection=False):
		"""
		You should only call this constructor with keyword arguments;
		due to inheritance, mixing and matching keyword and non-keyword is a bad idea.
		The first three arguments that are not keyword are taken as `field_name`,
		`interface` and `field_callable`.
		"""
		# sadly we can't reuse any of the defaults from the super classes, and we
		# must rely on the order of parameters
		super(NormalizationWrapper,self).__init__(field_name, interface, field_callable,
												  index, normalizer, is_collection)
