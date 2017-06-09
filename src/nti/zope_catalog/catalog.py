#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Catalog extensions.

"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import warnings

from zope.catalog.catalog import Catalog as _ZCatalog

from ZODB.POSException import POSError

import BTrees

from nti.zodb import isBroken

from nti.zope_catalog.interfaces import INoAutoIndex


class ResultSet(object):
    """
    Lazily accessed set of objects.

    This is just like :class:`zope.catalog.catalog.ResultSet`
    except it is slower (it has more overhead) and it offers the dubious
    feature of ignoring broken objects (which is a footgun if ever
    there was). If you have such objects, your code or deployment
    is broken.

    Prefer not to use this class in normal operations (it might be useful
    for recovery, but even that's doubtful since it doesn't track
    which objects were "invalid").
    """

    def __init__(self, uids, uidutil, ignore_invalid=False):
        self.uids = uids
        self.uidutil = uidutil
        self.ignore_invalid = ignore_invalid
        if ignore_invalid:
            warnings.warn("Please do not ignore corrupted databases.",
                          stacklevel=2)

    def __len__(self):
        return len(self.uids)

    def get_object(self, uid):
        if self.ignore_invalid:
            obj = self.uidutil.queryObject(uid)
            if isBroken(obj, uid):
                obj = None
        else:
            obj = self.uidutil.getObject(uid)
        if obj is None:
            logger.warn("Your database is corrupted. There is no object for id %d", uid)
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
        """
        How many objects are there?

        In a proper database, this should be identical to the
        len() of this object. This is only different if the database
        is corrupt and needs fixed. If you see this, this is a strong
        signal that your code is broken.
        """
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

    family = BTrees.family64

    def _visitAllSublocations(self):
        return super(Catalog, self)._visitSublocations()

    def _visitSublocations(self):
        for uid, obj in self._visitAllSublocations():
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
