 #!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Helpers for indexing strings.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from zc.catalog.interfaces import INormalizer
from zope import interface

from nti.zope_catalog.mixin import AbstractNormalizerMixin

__docformat__ = "restructuredtext en"



@interface.implementer(INormalizer)
class StringTokenNormalizer(AbstractNormalizerMixin):
    """
    A normalizer for strings that are treated like tokens:
    strings are lower-cased and guaranteed to be unicode
    and leading and trailing spaces are removed.

    This object accepts byte strings and decodes them using UTF-8.
    """

    def value(self, value):
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return value.lower().strip() if value else value
