#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Interfaces related to catalogs.

"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.catalog.interfaces import ICatalog
from zope.catalog.interfaces import INoAutoIndex
from zope.catalog.interfaces import INoAutoReindex

from zope.catalog.field import IFieldIndex as IZCVFieldIndex

from zope.catalog.keyword import IKeywordIndex as IZCKeywordIndex

from zope.catalog.text import ITextIndex as IZCTextIndex

from zc.catalog.interfaces import ISetIndex as IZCSetIndex
from zc.catalog.interfaces import IValueIndex as IZCValueIndex


class IZipMixin(interface.Interface):

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


class IMetadataCatalog(ICatalog):
    """
    The nti metadata catalog.
    """

    def index_doc(self, iid, ob):
        """
        This may or may not update our underlying index.
        """

    def force_index_doc(self, iid, ob):
        """
        Force the underlying index to update.
        """
