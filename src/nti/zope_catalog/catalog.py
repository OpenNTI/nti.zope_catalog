#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Catalog extensions.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.catalog.catalog import Catalog as _ZCatalog

from ZODB.interfaces import IBroken

from ZODB.POSException import POSError
from ZODB.POSException import POSKeyError

from .interfaces import INoAutoIndex

def is_broken(obj, uid=None):
	result = False
	try:
		if obj is None:
			logger.warn("Ignoring missing object %s", uid)
			result = (uid is not None)
		else:
			if hasattr(obj, '_p_activate'):
				obj._p_activate()
			result = IBroken.providedBy(obj)
	except POSError:	
		logger.error("Ignoring broken object %s, %s", type(obj), uid)
		result = True
	return result

class ResultSet(object):
	"""
	Lazily accessed set of objects.
	"""

	def __init__(self, uids, uidutil, ignore_invalid=False):
		self.uids = uids
		self.uidutil = uidutil
		self.ignore_invalid = ignore_invalid

	def __len__(self):
		return len(self.uids)

	def iter_pairs(self):
		for uid in self.uids:
			if self.ignore_invalid:
				obj = self.uidutil.queryObject(uid)
				if is_broken(obj, uid):
					obj = None
			else:
				obj = self.uidutil.getObject(uid)
			if obj is not None:
				yield uid, obj

	def __iter__(self):
		for _, obj in self.iter_pairs():
			yield obj
			
class Catalog(_ZCatalog):
	"""
	An extended catalog. Features include:

	* When manually calling :meth:`updateIndex` or
	  :meth:`updateIndexes`, objects that provide
	  :class:`.INoAutoIndex` are ignored. Note that if you have
	  previously indexed objects that now provide this (i.e., class
	  definition has changed) you need to :meth:`clear` the catalog
	  first for this to be effective.

	* Updating indexes can optionally ignore certain errors related to
	  persistence POSKeyErrors. Note that updating a single index does
	  this by default (since it is usually called from the
	  :class:`.IObjectAdded` event handler) but updating all indexes
	  does not since it is usually called by hand.
	"""

	def _visitSublocations(self):
		for uid, obj in super(Catalog,self)._visitSublocations():
			if INoAutoIndex.providedBy(obj):
				continue
			yield uid, obj

	# we may get TypeError: __setstate__() takes exactly 2 arguments (1 given)
	# error or creator cannot be resolved (if a user has been deleted)
	# catch and continue
	_PERSISTENCE_EXCEPTIONS = (POSKeyError, TypeError)

	# disable warning about different number of arguments than superclass
	# pylint: disable=I0011,W0221
	def updateIndex(self, index, ignore_persistence_exceptions=True):
		to_catch = self._PERSISTENCE_EXCEPTIONS if ignore_persistence_exceptions else ()
		for uid, obj in self._visitSublocations():
			try:
				index.index_doc(uid, obj)
			except to_catch as e:
				logger.error("Error indexing object %s(%s); %s", type(obj), uid, e)

	def updateIndexes(self, ignore_persistence_exceptions=False):
		indexes = list(self.values()) # avoid the btree iterator for each object
		to_catch = self._PERSISTENCE_EXCEPTIONS if ignore_persistence_exceptions else ()
		for uid, obj in self._visitSublocations():
			for index in indexes:
				try:
					index.index_doc(uid, obj)
				except to_catch as e:
					logger.error("Error indexing object %s(%s); %s", type(obj), uid, e)
