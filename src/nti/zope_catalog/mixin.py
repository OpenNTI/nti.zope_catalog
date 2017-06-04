#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


class AbstractNormalizerMixin(object):

    def any(self, value, index):
        return self.value(value),

    def all(self, value, index):
        return self.value(value)

    def minimum(self, value, index, exclude=False):
        return self.value(value)

    def maximum(self, value, index, exclude=False):
        return self.value(value)
