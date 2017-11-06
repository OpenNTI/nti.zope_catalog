#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Interfaces related to catalogs.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from zc.catalog.interfaces import ISetIndex as IZCSetIndex
from zc.catalog.interfaces import IValueIndex as IZCValueIndex
from zope.catalog.field import IFieldIndex as IZCVFieldIndex
from zope.catalog.interfaces import ICatalogEdit
from zope.catalog.interfaces import ICatalogIndex
from zope.catalog.interfaces import ICatalogQuery
from zope.catalog.interfaces import INoAutoIndex
from zope.catalog.interfaces import INoAutoReindex
from zope.catalog.keyword import IKeywordIndex as IZCKeywordIndex
from zope.catalog.text import ITextIndex as IZCTextIndex
import zope.container.constraints
from zope.container.interfaces import IContainer
from zope.interface import Interface

__docformat__ = "restructuredtext en"

# pylint:disable=inherit-non-class,no-self-argument,no-method-argument
# pylint:disable=too-many-ancestors

class IZipMixin(Interface):

    def zip(doc_ids=()):
        """
        return an iterator of doc_id, value pairs
        """


class INoAutoIndexEver(INoAutoIndex, INoAutoReindex):
    """
    Marker interface for objects that should not automatically
    be added to catalogs when created or modified events
    fire.
    """


class IKeywordIndex(IZCKeywordIndex, IZipMixin):

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


class IFieldIndex(IZCVFieldIndex, IZipMixin):

    def doc_value(doc_id):
        """
        return the value associated with the specified doc id
        """


class IValueIndex(IZCValueIndex, IZipMixin):
    pass


class ISetIndex(IZCSetIndex, IZipMixin):
    pass


class IIntegerValueIndex(IZCValueIndex, IZipMixin):
    pass


class ITextIndex(IZCTextIndex):
    pass

# It would be nice to write `IDeferredCatalog(*ICatalog.__bases__)`
# but Python 2 doesn't support that syntax, and calling InterfaceClass
# directly while specifying the container constraints is difficult/ugly.
class IDeferredCatalog(ICatalogQuery, ICatalogEdit, IContainer):
    """
    Just like :class:`~.ICatalog`, but a distinct interface to be able
    to distinguish it at runtime, typically in event subscribers.

    The use-case is for certain catalogs that want to defer indexing
    (sometimes to a separate process).  Implement this interface
    instead of :class:`~.ICatalog` so that the subscribers
    :func:`zope.catalog.catalog.indexDocSubscriber`,
    :func:`zope.catalog.catalog.unindexDocSubscriber`, and
    :func:`zope.catalog.catalog.reindexDocSubscriber` do not find and
    use this object.

    To search, you'll want to look for :class:`~.ICatalogQuery` which
    is implemented by both :class:`.ICatalog` and this object.

    To find every utility that can support indexing, you can look for
    :class:`zope.index.interfaces.IInjection` which is also
    implemented by both interfaces.

    As a base, instead of extending :class:`.Catalog`, you can extend
    :class:`.DeferredCatalog`.

    .. versionadded:: 2.0.0
    """

    zope.container.constraints.contains(ICatalogIndex)

IDeferredCatalog['__setitem__'].__doc__ = ''

#: Backwards compatibility alias.
IMetadataCatalog = IDeferredCatalog
