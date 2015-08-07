#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Interfaces related to catalogs.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.catalog.interfaces import INoAutoIndex
from zope.catalog.interfaces import INoAutoReindex
from zope.catalog.keyword import IKeywordIndex as IZCKeywordIndex

from zc.catalog.interfaces import IValueIndex as IZCValueIndex

class INoAutoIndexEver(INoAutoIndex, INoAutoReindex):
	"""
	Marker interface for objects that should not automatically
	be added to catalogs when created or modified events
	fire.
	"""

class IKeywordIndex(IZCKeywordIndex):
	
	def ids():
		"""
		return the docids in this Index
		"""
	
	def words():
		"""
		return the words in this Index
		"""

	def remove_words(*words):
		"""
		remove the specified sequence of words
		"""
		
class IValueIndex(IZCValueIndex):
	
	def zip(doc_ids=()):
		"""
		return an iterator of doc_id, value pairs
		"""
