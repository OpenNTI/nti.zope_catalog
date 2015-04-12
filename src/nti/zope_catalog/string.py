#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Helpers for indexing strings.

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope import interface

from zc.catalog.interfaces import INormalizer

from .datetime import _AbstractNormalizerMixin

@interface.implementer(INormalizer)
class StringTokenNormalizer(_AbstractNormalizerMixin):
	"""
	A normalizer for strings that are treated like tokens:
	strings are lower-cased and guaranteed to be unicode
	and leading and trailing spaces are removed.
	"""

	def value(self, value):
		if value is None:
			return
		if isinstance(value, bytes):
			value = value.decode('utf-8')
		return value.lower().strip()
