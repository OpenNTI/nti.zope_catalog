#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mixin base classes.
"""

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)


class AbstractNormalizerMixin(object):
    """
    Base class for normalizing values. All methods are directed to
    :meth:`value` by default; for more specific behaviour, override
    the corresponding method.
    """

    def any(self, value, index):
        return (self.value(value),)

    def all(self, value, index):
        return self.value(value)

    def minimum(self, value, index, exclude=False):
        return self.value(value)

    def maximum(self, value, index, exclude=False):
        return self.value(value)

    def value(self, value):
        """Normalize the given value for an arbitrary query."""
        raise NotImplementedError()
