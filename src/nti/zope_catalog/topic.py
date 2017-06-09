#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Support for writing topic indexes and the filtered sets that go with them.

"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import collections

from zope import interface

from zope.catalog.interfaces import ICatalogIndex

from zope.container.contained import Contained

from zope.index.topic import TopicIndex as _TopicIndex
from zope.index.topic.filter import FilteredSetBase

from zc.catalog.extentcatalog import FilterExtent

import BTrees


@interface.implementer(ICatalogIndex)
class TopicIndex(_TopicIndex, Contained):
    """
    A topic index that implements IContained and ICatalogIndex for use with
    catalog indexes.

    To summarize, a topic index is a way to divide objects into a set
    of groups (aka topics). The groups are determined by the contents
    of this object, which are called filters. Each filter is
    conceptually like a mini-index itself, but in practice most of
    them are simply used to store group membership when some criteria
    are met; for that purpose the :class:`.ExtentFilteredSet` is
    ideal.
    """

    #: We default to 64-bit btrees.
    family = BTrees.family64

    # If we're not IContained, we get location proxied.

    # If we're not ICatalogIndex, we don't get updated when
    # we get put in a catalog.

    def __getitem__(self, filterid):
        return self._filters[filterid]

    def apply(self, query):
        """
        Queries this index and returns the set of matching docids.

        The `query` can be in one of several formats:

        * A single string or a list of strings. In that case,
          docids that are in all the given topics (by id) are returned.
          This is equivalent to zc.catalog-style ``all_of`` operator.
        * A dictionary containing exactly two keys, ``operator``
          and ``query``. The value for ``operator`` is either
          ``and`` or ``or`` to specify intersection or union, respectively.
          The value for query is again a string or list of strings.
        * A dictionary containing exactly one key, either ``any_of``
          or ``all_of``, whose value is the string or list of string
          topic IDs.
        """
        # The first two cases are handled natively. The later case,
        # zc.catalog style, we handle by converting.
        if isinstance(query, collections.Mapping):
            if 'any_of' in query:
                query = {'operator': 'or', 'query': query['any_of']}
            elif 'all_of' in query:
                query = {'operator': 'and', 'query': query['all_of']}
        return super(TopicIndex, self).apply(query)


class ExtentFilteredSet(FilteredSetBase):
    """
    A filtered set that uses an :class:`zc.catalog.interfaces.IExtent`
    to store document IDs; this can make for faster, easier querying
    of other indexes.
    """

    #: We default to 64-bit btrees
    family = BTrees.family64

    #: The extent object. We pull this apart to
    #: get the value for `_ids` (used in the implementation
    #: of `unindex_doc`)
    _extent = None

    #: The set-like object that holds docids. In our case,
    #: this is an extent.
    _ids = None

    def __init__(self, fid, expr, family=None):
        """
        Create a new filtered extent.

        :param filter: A callable object of three parameters: this
                object, the docid, and the document. This will be
                available as the value of :meth:`getExpression`.
                If you pass `None`, you can override getExpression
                yourself.

                *Remember* that this is a persistent object, so if you
                pass a filter, it must be picklable. In general and for
                the most flexibility, instead of passing something like
                `IFoo.providedBy`, instead pass a global (function) object
                in your own module.
        """
        super(ExtentFilteredSet, self).__init__(fid, expr, family=family)
        # The super implementation calls clear() to establish `_ids`

    def ids(self):
        return tuple(self._ids) if self._ids is not None else ()

    def clear(self):
        # Note that we ignore the super implementation.
        self._extent = FilterExtent(self.getExpression(), family=self.family)
        self._ids = self._extent.set

    def index_doc(self, docid, context):
        try:
            self._extent.add(docid, context)
        except ValueError:
            self.unindex_doc(docid)

    def getExtent(self):
        """
        Returns the :class:`zc.catalog.interfaces.IFilterExtent` used.
        This is always consistent with the return value of :meth:`getIds`.
        """
        return self._extent
