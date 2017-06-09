#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import is_
from hamcrest import contains
from hamcrest import assert_that

import unittest

from nti.zope_catalog.number import number_to_64bit_int
from nti.zope_catalog.number import FloatTo64BitIntNormalizer
from nti.zope_catalog.number import FloatToNormalized64BitIntNormalizer

from nti.zope_catalog.index import IntegerValueIndex
from nti.zope_catalog.index import NormalizationWrapper


class TestNumber(unittest.TestCase):

    field = 1

    def test_int_normalizer(self):
        assert_that(FloatTo64BitIntNormalizer().value(-123456.78),
                    is_(-4540151738323089490))
        assert_that(FloatTo64BitIntNormalizer().original_value(-4540151738323089490),
                    is_(-123456.78))

    def test_combined_normalizer(self):
        orig = 123456.78
        value_normalized = number_to_64bit_int(123456.78)
        normalizer = FloatToNormalized64BitIntNormalizer()
        assert_that(normalizer.value(orig), is_(value_normalized))

    def test_combined_normalizer_query(self):
        orig = 123456.78
        normalizer = FloatToNormalized64BitIntNormalizer()

        index = NormalizationWrapper('field', index=IntegerValueIndex(),
                                     normalizer=normalizer)

        self.field = orig
        index.index_doc(1, self)

        # Exact-match query for the original value
        assert_that(index.apply((orig, orig)),
                    contains(1))

        # between query for the normalized value
        assert_that(index.apply({'between': (orig,)}),
                    contains(1))
