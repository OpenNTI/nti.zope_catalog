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

from nti.zope_catalog.interfaces import INoAutoIndex


def isBroken(obj, uid=None):
    result = False
    try:
        if obj is None:
            msg = uid if uid is not None else u''
            logger.debug("Ignoring NULL object %s", msg)
            result = (uid is not None)
        else:
            try:
                obj._p_activate()
            except (TypeError, AttributeError):
                pass
            result = IBroken.providedBy(obj)
    except (POSError, TypeError):
        logger.error("Ignoring broken object %s, %s", type(obj), uid)
        result = True
    return result
is_broken = isBroken


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

    def get_object(self, uid):
        if self.ignore_invalid:
            obj = self.uidutil.queryObject(uid)
            if isBroken(obj, uid):
                obj = None
        else:
            obj = self.uidutil.queryObject(uid)
        return obj
    getObject = get_object

    def items(self):
        for uid in self.uids:
            obj = self.get_object(uid)
            if obj is not None:
                yield uid, obj
    iter_pairs = items

    def __iter__(self):
        for _, obj in self.items():
            yield obj

    def count(self):
        result = 0
        for _, _ in self.items():
            result += 1
        return result


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
        for uid, obj in super(Catalog, self)._visitSublocations():
            if INoAutoIndex.providedBy(obj):
                continue
            yield uid, obj

    # we may get TypeError: __setstate__() takes exactly 2 arguments (1 given)
    # error or creator cannot be resolved (if a user has been deleted)
    # catch and continue
    _PERSISTENCE_EXCEPTIONS = (POSError, TypeError)

    # disable warning about different number of arguments than superclass
    # pylint: disable=I0011,W0221
    def updateIndex(self, index, ignore_persistence_exceptions=True):
        to_catch = self._PERSISTENCE_EXCEPTIONS if ignore_persistence_exceptions else ()
        for uid, obj in self._visitSublocations():
            try:
                index.index_doc(uid, obj)
            except to_catch as e:
                logger.error("Error indexing object %s(%s); %s",
                             type(obj), uid, e)

    def updateIndexes(self, ignore_persistence_exceptions=False):
        # avoid the btree iterator for each object
        indexes = list(self.values())
        to_catch = self._PERSISTENCE_EXCEPTIONS if ignore_persistence_exceptions else ()
        for uid, obj in self._visitSublocations():
            for index in indexes:
                try:
                    index.index_doc(uid, obj)
                except to_catch as e:
                    logger.error("Error indexing object %s(%s); %s",
                                 type(obj), uid, e)
