#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import contains
from hamcrest import assert_that
from hamcrest import contains_inanyorder

import time
import datetime
import unittest

from nti.zodb.containers import time_to_64bit_int

from nti.zope_catalog.datetime import TimestampNormalizer
from nti.zope_catalog.datetime import TimestampTo64BitIntNormalizer
from nti.zope_catalog.datetime import TimestampToNormalized64BitIntNormalizer

from nti.zope_catalog.index import IntegerValueIndex
from nti.zope_catalog.index import NormalizationWrapper


class TestDatetime(unittest.TestCase):

    field = 1

    def test_int_normalizer(self):
        assert_that(TimestampTo64BitIntNormalizer().value(123456.78),
                    is_(4683220298531686318))

    def test_timestamp_normalizer(self):
        orig = datetime.datetime(2014, 2, 24, 12, 30, 7, 650261)
        orig = time.mktime(orig.timetuple())

        minute_normalized = datetime.datetime(2014, 2, 24, 12, 30)
        minute_normalized = time.mktime(minute_normalized.timetuple())

        hour_normalized = datetime.datetime(2014, 2, 24, 12)
        hour_normalized = time.mktime(hour_normalized.timetuple())

        normalizer = TimestampNormalizer()

        # default to minute
        assert_that(normalizer.value(orig), is_(minute_normalized))

        # change resolution
        normalizer.resolution = normalizer.RES_HOUR
        assert_that(normalizer.value(orig), is_(hour_normalized))

    def test_combined_normalizer(self):
        orig = datetime.datetime(2014, 2, 24, 12, 30, 7, 650261)
        orig = time.mktime(orig.timetuple())

        minute_normalized = datetime.datetime(2014, 2, 24, 12, 30)
        minute_normalized = time.mktime(minute_normalized.timetuple())
        minute_normalized = time_to_64bit_int(minute_normalized)

        hour_normalized = datetime.datetime(2014, 2, 24, 12)
        hour_normalized = time.mktime(hour_normalized.timetuple())
        hour_normalized = time_to_64bit_int(hour_normalized)

        normalizer = TimestampToNormalized64BitIntNormalizer()

        # default to minute
        assert_that(normalizer.value(orig), is_(minute_normalized))

        # change resolution
        normalizer.resolution = TimestampNormalizer.RES_HOUR
        assert_that(normalizer.value(orig), is_(hour_normalized))

    def test_combined_normalizer_query(self):
        orig = datetime.datetime(2014, 2, 24, 12, 30, 7, 650261)
        orig = time.mktime(orig.timetuple())

        minute_normalized = datetime.datetime(2014, 2, 24, 12, 30)
        minute_normalized_time = time.mktime(minute_normalized.timetuple())
        minute_normalized = time_to_64bit_int(minute_normalized_time)

        hour_normalized = datetime.datetime(2014, 2, 24, 12)
        hour_normalized_time = time.mktime(hour_normalized.timetuple())
        hour_normalized = time_to_64bit_int(hour_normalized_time)

        normalizer = TimestampToNormalized64BitIntNormalizer()

        index = NormalizationWrapper('field', index=IntegerValueIndex(),
                                     normalizer=normalizer)

        self.field = orig

        index.index_doc(1, self)

        # Exact-match query for the original value
        assert_that(index.apply((orig, orig)),
                    contains(1))

        # exact-match query for the normalized value
        assert_that(index.apply((minute_normalized_time, minute_normalized_time)),
                    contains(1))

        # range query, beginning time only
        assert_that(index.apply({'between': (hour_normalized_time,)}),
                    contains(1))

        self.field = 1234
        index.index_doc(2, self)

        assert_that(index.apply({'any': None}),
                    contains_inanyorder(1, 2))

        assert_that(list(index.sort((2, 1))),
                    contains(2, 1))

class TestTimestampNormalizer(unittest.TestCase):

    def test_normalizes_datetime(self):
        orig = datetime.datetime(2014, 2, 24, 12, 30, 7, 650261)
        minute_normalized = datetime.datetime(2014, 2, 24, 12, 30)
        normalizer = TimestampNormalizer()

        assert_that(normalizer.value(orig),
                    is_(time.mktime(minute_normalized.timetuple())))

        # The methods we inherit but don't implement. See the extensive
        # comment in the class.
        assert_that(normalizer.any(orig, None),
                    is_((time.mktime(minute_normalized.timetuple()),)))
        assert_that(normalizer.all(orig, None),
                    is_(time.mktime(minute_normalized.timetuple())))
        assert_that(normalizer.minimum(orig, None),
                    is_(time.mktime(minute_normalized.timetuple())))
        assert_that(normalizer.maximum(orig, None),
                    is_(time.mktime(minute_normalized.timetuple())))
