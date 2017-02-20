#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Helpers for indexing strings.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zc.catalog.interfaces import INormalizer

from nti.zope_catalog.datetime import _AbstractNormalizerMixin

try:
    _unicode = unicode
except NameError:  # python 3
    _unicode = lambda s: s


def to_unicode(s, encoding='utf-8', err='strict'):
    s = s.decode(encoding, err) if isinstance(s, bytes) else s
    return _unicode(s) if s is not None else None


@interface.implementer(INormalizer)
class StringTokenNormalizer(_AbstractNormalizerMixin):
    """
    A normalizer for strings that are treated like tokens:
    strings are lower-cased and guaranteed to be unicode
    and leading and trailing spaces are removed.
    """

    def value(self, value):
        value = to_unicode(value) if value is not None else None
        return value.lower().strip() if value is not None else None
