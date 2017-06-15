#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Normalization of numbers.
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zope.cachedescriptors.property import CachedProperty

from zc.catalog.interfaces import INormalizer

from persistent import Persistent

from nti.zodb.containers import bit64_int_to_time as bit64_int_to_number
from nti.zodb.containers import time_to_64bit_int  as number_to_64bit_int

from nti.zope_catalog.mixin import AbstractNormalizerMixin


@interface.implementer(INormalizer)
class FloatTo64BitIntNormalizer(AbstractNormalizerMixin):
    """
    Normalizes incoming floating point objects to 64-bit integers.
    Use this with a
    :class:`zc.catalog.catalogindex.NormalizationWrapper`. Note
    that when you do so, the values returned by a method like
    :meth:`zc.catalog.interfaces.IIndexValues` will be integer
    representations, not floating point timestamps.
    """

    __slots__ = ()

    def value(self, value):
        return number_to_64bit_int(value)

    def original_value(self, value):
        return bit64_int_to_number(value)


@interface.implementer(INormalizer)
class FloatToNormalized64BitIntNormalizer(Persistent,
                                          AbstractNormalizerMixin):
    """
    Normalizes incoming float values to integers so
    that can be stored in an :class:`nti.zodb_catalog.field.IntegerAttributeIndex`.
    """

    @CachedProperty
    def _int_normalizer(self):
        return FloatTo64BitIntNormalizer()

    def value(self, value):
        return self._int_normalizer.value(value)
