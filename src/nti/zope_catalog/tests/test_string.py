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

from nti.zope_catalog.index import NormalizationWrapper

from nti.zope_catalog.string import StringTokenNormalizer


class TestStringNormalizer(unittest.TestCase):

    field = 'ABC'

    def test_value(self):
        assert_that(StringTokenNormalizer().value(b'ABC'),
                    is_('abc'))
        assert_that(StringTokenNormalizer().value(u'ABC'),
                    is_('abc'))

    def test_index_search(self):
        from zc.catalog.index import ValueIndex

        index = NormalizationWrapper('field',
                                     index=ValueIndex(),
                                     normalizer=StringTokenNormalizer())

        index.index_doc(1, self)

        assert_that(index.values(),
                    contains('abc'))

        assert_that(index.apply(('ABC', 'ABC')),
                    contains(1))
