#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, absolute_import, division
__docformat__ = "restructuredtext en"

import zope.component.testlayer
import nti.zope_catalog

NTIZopeCatalogLayer = zope.component.testlayer.ZCMLFileLayer(nti.zope_catalog, 'configure.zcml')
