#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Support efficiently storing datetime values in an index, normalized.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import time
from pytz import UTC
from datetime import datetime

from zope import interface

from zc.catalog.interfaces import INormalizer
from zc.catalog.index import DateTimeNormalizer

from persistent import Persistent

from nti.common.time import time_to_64bit_int
from nti.common.time import bit64_int_to_time

from nti.common.property import CachedProperty

class _AbstractNormalizerMixin(object):

	def any(self, value, index):
		return self.value(value),

	def all(self, value, index):
		return self.value(value)

	def minimum(self, value, index, exclude=False):
		return self.value(value)

	def maximum(self, value, index, exclude=False):
		return self.value(value)

@interface.implementer(INormalizer)
class TimestampTo64BitIntNormalizer(_AbstractNormalizerMixin):
	"""
	Normalizes incoming floating point objects representing Unix
	timestamps to 64-bit integers. Use this with a
	:class:`zc.catalog.catalogindex.NormalizationWrapper`. Note
	that when you do so, the values returned by a method like
	:meth:`zc.catalog.interfaces.IIndexValues` will be integer
	representations, not floating point timestamps.
	"""
	__slots__ = ()

	def value(self, value):
		return time_to_64bit_int(value)

	def original_value(self, value):
		return bit64_int_to_time(value)

@interface.implementer(INormalizer)
class TimestampNormalizer(Persistent, _AbstractNormalizerMixin):
	"""
	Normalizes incoming Unix timestamps to have a set
	resolution, by default minutes.
	"""

	# These values wind up corresponding to the
	# indices in the timetuple

	RES_DAY = 0
	RES_HOUR = 1
	RES_MINUTE = 2
	RES_SECOND = 3
	RES_MICROSECOND = 4

	def __init__(self, resolution=RES_MINUTE):
		self.resolution = resolution

	@CachedProperty('resolution')
	def _datetime_normalizer(self):
		return DateTimeNormalizer(self.resolution)

	def value(self, value):
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
class TimestampToNormalized64BitIntNormalizer(Persistent, _AbstractNormalizerMixin):
	"""
	Normalizes incoming Unix timestamps to have a set resolution,
	by default minutes, and then converts them to integers
	that can be stored in an :class:`nti.zodb_catalog.field.IntegerAttributeIndex`.
	"""

	def __init__(self, resolution=TimestampNormalizer.RES_MINUTE):
		self.resolution = resolution

	@CachedProperty('resolution')
	def _timestamp_normalizer(self):
		return TimestampNormalizer(self.resolution)

	@CachedProperty
	def _int_normalizer(self):
		return TimestampTo64BitIntNormalizer()

	def value(self, value):
		return self._int_normalizer.value(
					self._timestamp_normalizer.value(value))
