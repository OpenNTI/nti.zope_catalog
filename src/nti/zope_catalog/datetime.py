#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Support efficiently storing datetime values in an index, normalized.

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

# stdlib imports
from datetime import datetime
import time

from persistent import Persistent
from pytz import UTC
from zc.catalog.index import DateTimeNormalizer
from zc.catalog.interfaces import INormalizer
from zope import interface
from zope.cachedescriptors.property import CachedProperty

from nti.zope_catalog.mixin import AbstractNormalizerMixin
from nti.zope_catalog.number import FloatTo64BitIntNormalizer

__docformat__ = "restructuredtext en"


@interface.implementer(INormalizer)
class TimestampNormalizer(Persistent, AbstractNormalizerMixin):
    """
    Normalizes incoming Unix timestamps (or datetimes) to have a set
    resolution, by default minutes.
    """

    # These values wind up corresponding to the
    # indices in the timetuple

    #: Constant for normalizing to days.
    RES_DAY = 0
    #: Constant for normalizing to hours.
    RES_HOUR = 1
    #: Constant for normalizing to minutes.
    RES_MINUTE = 2
    #: Constant for normalizing to seconds.
    RES_SECOND = 3
    #: Constant for normalizing to microseconds.
    RES_MICROSECOND = 4

    def __init__(self, resolution=RES_MINUTE):
        self.resolution = resolution

    @CachedProperty('resolution')
    def _datetime_normalizer(self):
        return DateTimeNormalizer(self.resolution)

    def value(self, value):
        """
        Normalize to a floating point value.

        .. versionchanged:: 1.0.0
           Incoming datetimes are also normalized.
        """
        if isinstance(value, datetime):
            dt = value
        else:
            dt = datetime.fromtimestamp(value)

        dt = dt.replace(tzinfo=UTC)
        dt = self._datetime_normalizer.value(dt)
        return time.mktime(dt.timetuple())

    # The provided date-time normalizer supports taking
    # datetime.date objects for the various range queries
    # and turning those into sequences. For example, if you ask
    # for 'any' on July 4, you get a normalized query that is all
    # datetime values in the index from July 0, 00:00 to July 4 23:59.
    # We could do that too, if we need to, but for the moment we don't care
    # because we don't do these kind of searches with this index...?


@interface.implementer(INormalizer)
class TimestampTo64BitIntNormalizer(TimestampNormalizer):
    """
    Normalizes incoming Unix timestamps to have a set resolution,
    by default minutes, and then converts them to integers
    that can be stored in an :class:`.IntegerAttributeIndex`.

    .. versionchanged:: 2.0.0
       Now subclass :class:`TimestampNormalizer` and rework some internal
       attributes.
    .. versionchanged:: 2.0.0
       Rename from ``TimestampToNormalized64BitIntNormalizer`` to
       ``TimestampTo64BitIntNormalizer``. Previously, :class:`.FloatTo64BitIntNormalizer`
       was imported under this name.
    """

    _int_normalizer = FloatTo64BitIntNormalizer()

    def value(self, value):
        float_norm = TimestampNormalizer.value(self, value)
        return self._int_normalizer.value(float_norm)

#: Backwards compatibility alias.
TimestampToNormalized64BitIntNormalizer = TimestampTo64BitIntNormalizer
