#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Support for working with :class:`zope.catalog.field` indexes.

All of the indexes we define are compatible with both
:mod:`zope.catalog` query syntax (and internal attributes) and :mod:`zc.catalog`
syntax (and public attributes).
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six
import collections

from zope import interface

from zope.catalog.attribute import AttributeIndex

from zope.catalog.interfaces import ICatalogIndex

from zope.catalog.text import TextIndex

from zope.container.contained import Contained

import zope.index.field
import zope.index.keyword
from zope.index.text import lexicon

import zc.catalog.index
import zc.catalog.stemmer
import zc.catalog.catalogindex

import BTrees

from nti.property.property import alias

from nti.zope_catalog.interfaces import ISetIndex
from nti.zope_catalog.interfaces import ITextIndex
from nti.zope_catalog.interfaces import IFieldIndex
from nti.zope_catalog.interfaces import IValueIndex
from nti.zope_catalog.interfaces import IKeywordIndex
from nti.zope_catalog.interfaces import IIntegerValueIndex


def is_nonstr_iter(x):
    return not isinstance(x, six.string_types) \
        and isinstance(x, collections.Iterable)


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
        return super(_ZCApplyMixin, self).apply(query)


class _ZCAbstractIndexMixin(object):
    """
    Helpers and compatibility mixins for zope.catalog and zc.catalog.
    Makes zc.catalog indexes look a bit more like zope.catalog indexes.
    """

    family = BTrees.family64
    _num_docs = alias('documentCount')
    _fwd_index = alias('values_to_documents')
    _rev_index = alias('documents_to_values')


class _ZipMixin(object):

    def zip(self, doc_ids=()):
        for doc_id in doc_ids or ():
            value = self._rev_index.get(doc_id)
            yield doc_id, value

class _SetZipMixin(_ZipMixin):

    def zip(self, *args, **kwargs):
        for d, v in _ZipMixin.zip(self, *args, **kwargs):
            # TODO: Should we really be doing this? The values
            # are usually [OO]TreeSet, which is more memory and persistence
            # friendly
            yield d, set(v) if v is not None else None

@interface.implementer(IFieldIndex)
class NormalizingFieldIndex(_ZipMixin,
                            zope.index.field.FieldIndex,
                            Contained):
    """
    A field index that normalizes before indexing or searching.

    .. note:: For more flexibility, use a :class:`~.NormalizationWrapper`.
    """

    # We default to 64-bit trees
    family = BTrees.family64

    def normalize(self, value):
        "Subclasses must override this method."
        raise NotImplementedError()

    def index_doc(self, docid, value):
        super(NormalizingFieldIndex, self).index_doc(
            docid, self.normalize(value))

    def apply(self, query):
        query = tuple(self.normalize(x) for x in query)
        return super(NormalizingFieldIndex, self).apply(query)

    def ids(self):
        return self._rev_index.keys()

    def doc_value(self, doc_id):
        result = self._rev_index.get(doc_id)
        return result



class CaseInsensitiveAttributeFieldIndex(AttributeIndex,
                                         NormalizingFieldIndex):
    """
    An attribute index that normalizes case. It is queried with a
    two-tuple giving the min and max values.
    """

    def normalize(self, value):
        value = value.lower() if value else value
        return value

# Normalizing and wrappers:
# The normalizing code needs to get the actual values. Because AttributeIndex
# gets the attribute value in index_doc and then calls the same method on super
# with that returned value, the NormalizationWrapper has to extend AttributeIndex
# to get the right value to pass to the normamlizer. That means it cannot be used
# to wrap another AttributeIndex, only a plain ValueIndex or SetIndex. Note
# that it is somewhat painful to construct


@interface.implementer(IValueIndex)
class ValueIndex(_ZCApplyMixin,
                 _ZCAbstractIndexMixin,
                 _ZipMixin,
                 zc.catalog.index.ValueIndex):
    "An index of raw values."


class AttributeValueIndex(ValueIndex,
                          zc.catalog.catalogindex.ValueIndex):
    "An index of values stored in a particular attribute."


@interface.implementer(ISetIndex)
class SetIndex(_ZCAbstractIndexMixin,
               _SetZipMixin,
               zc.catalog.index.SetIndex):

    "An index of values that are multiple."

class AttributeSetIndex(SetIndex,
                        zc.catalog.catalogindex.SetIndex):
    "An index of values that are multiple and stored in an attribute."


@interface.implementer(IIntegerValueIndex)
class IntegerValueIndex(_ZCApplyMixin,
                        _ZCAbstractIndexMixin,
                        _ZipMixin,
                        zc.catalog.index.ValueIndex):
    """
    A "raw" index that is optimized for, and only supports,
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
class NormalizingKeywordIndex(_SetZipMixin,
                              zope.index.keyword.CaseInsensitiveKeywordIndex,
                              Contained):
    """
    A case-insensitive keyword index supporting traditional
    queries as well as extent-based queries.
    """

    family = BTrees.family64

    def _parseQuery(self, query):
        if isinstance(query, collections.Mapping):
            if 'query' in query:  # support legacy
                query_type = query.get('operator') or 'and'
                query = query['query']
            elif len(query) > 1:
                raise ValueError('may only pass one of key, value pair')
            elif not query:
                return None, None
            else:
                query_type, query = next(iter(query.items()))
                query_type = query_type.lower()
        elif isinstance(query, six.string_types):
            query_type = 'and'
        elif zc.catalog.interfaces.IExtent.providedBy(query):
            # This is iterable, so must go before that test.
            query_type = 'none'
        elif is_nonstr_iter(query):
            query_type = 'and'
        else:
            raise ValueError('Invalid query')

        if query_type not in ('any', 'none'):
            query = list(query) if is_nonstr_iter(query) else [query]
            query = [x for x in query if isinstance(x, six.string_types)]
            if not query:
                query_type, query = None, None
            elif query_type == 'any_of':
                query_type = 'or'
            elif query_type == 'all':
                query_type = 'and'
        return query_type, query

    def apply(self, query):  # any_of, any, between, none,
        query = convertQuery(query)
        query_type, query = self._parseQuery(query)
        if query_type is None:
            res = self.family.IF.Set()
        elif query_type in ('or', 'and'):
            res = super(NormalizingKeywordIndex, self).search(
                query, operator=query_type)
        elif query_type in ('between',):
            query = list(self._fwd_index.iterkeys(query[0], query[1]))
            res = super(NormalizingKeywordIndex, self).search(
                query, operator='or')
        elif query_type == 'none':
            assert zc.catalog.interfaces.IExtent.providedBy(query)
            res = query & self.family.IF.Set(self.ids())
        elif query_type == 'any':
            if query is None:
                res = self.family.IF.Set(self.ids())
            else:
                assert zc.catalog.interfaces.IExtent.providedBy(query)
                res = query & self.family.IF.Set(self.ids())
        else:
            raise ValueError("unknown query type", query_type) # pragma: no cover (can't get here)
        return res

    def ids(self):
        return self._rev_index.keys()

    def words(self):
        return self._fwd_index.keys()

    def remove_words(self, *seq):
        # XXX: Why does this method exist?
        # Why don't we just unindex the docs?
        seq = self.normalize(*seq)
        for word in seq:
            try:
                docids = self._fwd_index[word]
            except KeyError:
                pass
            else:
                del self._fwd_index[word]
                for docid in docids:
                    try:
                        s = self._rev_index[docid]
                    except KeyError:
                        logger.exception("Your index is corrupted: %s", word)
                    else:
                        s.remove(word)
                        if not s:
                            del self._rev_index[docid]
                            self._num_docs.change(-1)
    removeWords = remove_words



class AttributeKeywordIndex(AttributeIndex, NormalizingKeywordIndex):
    """An index for keywords stored in an attribute."""


@interface.implementer(ICatalogIndex)  # The superclass forgets this
class NormalizationWrapper(_ZCApplyMixin,
                           zc.catalog.catalogindex.NormalizationWrapper):
    """
    An attribute index that wraps a raw index and normalizes values.

    This class exists mainly to sort out the difficulty constructing
    instances by only accepting keyword arguments.
    """

    def __init__(self, field_name=None, interface=None, field_callable=False,
                 index=None, normalizer=None, is_collection=False):
        """
        You should only call this constructor with keyword arguments;
        due to inheritance, mixing and matching keyword and non-keyword is a bad idea.
        The first three arguments that are not keyword are taken as `field_name`,
        `interface` and `field_callable`.
        """
        # sadly we can't reuse any of the defaults from the super classes, and we
        # must rely on the order of parameters
        super(NormalizationWrapper, self).__init__(field_name, interface, field_callable,
                                                   index, normalizer, is_collection)


# text


def stemmer_lexicon(lang='english', stopwords=True):
    """
    A lexicon for text indexes using zc.catalog.
    """
    pipeline = [
        lexicon.Splitter(),
        lexicon.CaseNormalizer(),
    ]
    if stopwords:
        pipeline.append(lexicon.StopWordRemover())
    pipeline.append(zc.catalog.stemmer.Stemmer(lang))
    return lexicon.Lexicon(*pipeline)


@interface.implementer(ITextIndex)
class AttributeTextIndex(TextIndex):
    """A 64-bit text index.

    Example::

        index = AttributeTextIndex('field',
                                   lexicon=stemmer_lexicon())

    """

    #: We default to 64-bit btrees.
    family = BTrees.family64
