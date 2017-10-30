#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mixin base classes.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

__docformat__ = "restructuredtext en"


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
