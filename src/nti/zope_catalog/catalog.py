#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Catalog extensions.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# stdlib imports
import collections
import itertools
import warnings

import BTrees
from ZODB.POSException import POSError
from zope import interface
from zope.catalog.catalog import Catalog as _ZCatalog
from zope.catalog.interfaces import ICatalog

from nti.zodb import isBroken
from .interfaces import INoAutoIndex
from .interfaces import IDeferredCatalog


__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


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

    __length_hint__ = __len__

    def get_object(self, uid):
        if self.ignore_invalid:
            obj = self.uidutil.queryObject(uid)
            if isBroken(obj, uid):
                obj = None
        else:
            obj = self.uidutil.getObject(uid)
        if obj is None:
            logger.warning("Your database is corrupted. There is no object for id %d", uid)
        return obj
    getObject = get_object

    def items(self):
        for uid in self.uids:
            obj = self.get_object(uid)
            if obj is not None:
                yield uid, obj
    iter_pairs = items

    def __iter__(self):
        return (item[1] for item in self.items())

    def count(self):
        """
        How many objects are there?

        In a proper database, this should be identical to the
        len() of this object. This is only different if the database
        is corrupt and needs fixed. If you see this, this is a strong
        signal that your code is broken.
        """
        return sum(1 for _ in self.items())


class CatalogPrefetchIterator(object):
    """
    Given an iterator of ``(intid, object)``:

        - Breaks the iterator into chunks of a given size;

        - Detects any persistent objects in the chunk connected to a
          jar (this is done by checking for a ``_p_jar``);

        - Groups those objects by jar if needed (supporting multiple
          databases, because `ZODB 5 currently does not correctly do
          this <https://github.com/zopefoundation/ZODB/issues/273>`_);

        - Asks each jar to prefetch the given objects.

        - Finally, iterates over the chunk.

    This object is intended to be used with the ``_visitSublocations`` method
    of a catalog, but may be useful in other cases.

    For example, one could enhance a standard :class:`zope.catalog.catalog.ResultSet`
    like so (note this won't work for the :class:`ResultSet` defined here)::

        from zope.catalog.catalog import ResultSet
        class PrefetchedResultSet(ResultSet, object):
            def __iter__(self):
                iterable = (uid, self.uidutil.getObject(uid) for uid in self.uids)
                for _, obj in CatalogPrefetchIterator(iterable, 512):
                    yield obj


    .. versionadded:: 3.0
    """

    def __init__(self, iterable, chunk_size):
        self.iterable = iter(iterable) # work if they pass a concrete collection
        self.chunk_size = chunk_size
        self._chunk = None
        # The common case is that we only ever encounter one database;
        # the first time we see any jar, we'll know if we need to divy
        # objects between different jars or not.
        self._prefetch = self._prefetch_unknown
        self._single_jar = None

    def __iter__(self):
        return self

    def __next__(self):
        if not self._chunk:
            self._get_next_chunk()
        if not self._chunk:
            raise StopIteration

        return self._chunk.pop()

    next = __next__ # Python 2

    def _get_next_chunk(self, _islice=itertools.islice):
        if self.iterable is None:
            self._chunk = None
            return

        raw_chunk = list(_islice(self.iterable, self.chunk_size))
        self._prefetch(raw_chunk)
        self._chunk = raw_chunk
        if not raw_chunk or len(raw_chunk) < self.chunk_size:
            # We're done.
            self.iterable = None # Signal that to __next__
            self._prefetch = None # break the cycle
            self._single_jar = None # why not

    def _prefetch_unknown(self, raw_chunk):
        for _, obj in raw_chunk:
            jar = getattr(obj, '_p_jar', None)
            if jar is not None:
                # Hey hey, now we can find out if we need to
                # actually group or not.
                if len(jar.db().databases) > 1:
                    self._prefetch = self._prefetch_multidb
                else:
                    self._prefetch = self._prefetch_singledb
                    self._single_jar = jar
                self._prefetch(raw_chunk)
                # We have our answer we can quit now.
                break
        # We never encountered a persistent object. How sad.

    def _prefetch_multidb(self, raw_chunk, _defaultdict=collections.defaultdict):
        by_jar = _defaultdict(set) # {jar: [oids]}
        for _, obj in raw_chunk:
            jar = getattr(obj, '_p_jar', None)
            by_jar[jar].add(getattr(obj, '_p_oid', None))

        by_jar.pop(None) # lose the non-persistent objects
        for jar, oids in by_jar.items():
            oids.discard(None) # Lose persistent objects that aren't saved
            jar.prefetch(oids)

    def _prefetch_singledb(self, raw_chunk):
        oids = {
            getattr(obj, '_p_oid', None)
            for _, obj
            in raw_chunk
        }
        oids.discard(None) # lose the non-persistent objects, and those not saved
        self._single_jar.prefetch(oids)


class Catalog(_ZCatalog):
    """
    An extended catalog. Features include:

    * When manually calling :meth:`updateIndex` or
      :meth:`updateIndexes`, objects that provide
      :class:`nti.zope_catalog.interfaces.INoAutoIndex` are ignored.
      Note that if you have
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

    PREFETCH_CHUNK_SIZE = 512

    def _visitAllSublocations(self):
        return super(Catalog, self)._visitSublocations()

    def _visitSublocations(self):
        no_auto_inst = INoAutoIndex.providedBy
        no_auto_class = INoAutoIndex.implementedBy
        # Try to avoid activating the object if not necessary
        # by first checking if the class is INoAutoIndex.
        # We'll just need to check instances down below.
        no_auto_class_sublocations = (
            x
            for x in self._visitAllSublocations()
            if not no_auto_class(type(x[1]))
        )
        prefetched = CatalogPrefetchIterator(no_auto_class_sublocations,
                                             self.PREFETCH_CHUNK_SIZE)

        for uid, obj in prefetched:
            if no_auto_inst(obj):
                continue
            yield uid, obj

    # we may get TypeError: __setstate__() takes exactly 2 arguments (1 given)
    # error or creator cannot be resolved (if a user has been deleted)
    # catch and continue
    _PERSISTENCE_EXCEPTIONS = (POSError, TypeError)

    # disable warning about different number of arguments than superclass
    # pylint: disable=I0011,W0221
    def updateIndex(self, index, ignore_persistence_exceptions=True):
        """
        Update a single index.
        """
        to_catch = self._PERSISTENCE_EXCEPTIONS if ignore_persistence_exceptions else ()
        for uid, obj in self._visitSublocations():
            try:
                index.index_doc(uid, obj)
            except to_catch as e:
                logger.error("Error indexing object %s(%s); %s",
                             type(obj), uid, e)

    def updateIndexes(self, ignore_persistence_exceptions=False):
        """
        Update all indexes in this catalog.
        """
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

class DeferredCatalog(Catalog):
    """
    An implementation of :class:`nti.zope_catalog.interfaces.IDeferredCatalog`.
    """

_implemented_by = list(interface.implementedBy(DeferredCatalog).interfaces())
_implemented_by.remove(ICatalog)
_implemented_by.insert(0, IDeferredCatalog)

interface.classImplementsOnly(DeferredCatalog,
                              *_implemented_by)

del _implemented_by
