=========
 Changes
=========

4.1.0 (2024-11-12)
==================

- Drop support for Python 3.9.
- Use native namespace packages.


4.0.0 (2024-10-11)
==================

- Drop support for Python 2. We now only support Python 3.9 and above.
- Add support for Python 3.10, 11, 12, and 13.
- Remove dependency on ``zopyx.txng3.ext``.
- Remove dependency on ``pkg_resources``.


3.0.1 (2021-05-13)
==================

- Fix the ``ExtentFilteredSet`` to only unindex documents that were
  previously indexed. This avoids an extra ``readCurrent`` call. See
  `issue 12 <https://github.com/NextThought/nti.zope_catalog/issues/12>`_.


3.0.0 (2021-05-12)
==================

- Add support for Python 3.7, 3.8 and 3.9.

  Note that ``zopyx.txng3.ext`` version 4.0.0, the current version at
  this writing, may or may not build on CPython 3, depending on how
  your compiler and compiler options treat undefined functions.
  See `this issue <https://github.com/zopyx/zopyx.txng3.ext/issues/10>`_.

  Also note that both PyPy 3.6 and 3.7 (7.3.4) are known to crash when
  running the test suite. PyPy2 7.3.4 runs the test suite fine.

- When updating indexes in a catalog, first check if the type of each
  object to be visited implements ``INoAutoIndex``. If it does, we can
  avoid prematurely activating persistent ghost objects. See `issue 8
  <https://github.com/NextThought/nti.zope_catalog/issues/8>`_.

- Require ZODB 5 in order to use the new ``prefetch()`` method.

- When adding or updating an index in a catalog, use ZODB's prefetch
  method to grab chunks of object state data from the database. This
  can be substantially faster than making requests one at a time. This
  introduces a new class ``CatalogPrefetchIterator`` that may be
  useful in other circumstances. See `issue 7
  <https://github.com/NextThought/nti.zope_catalog/issues/8>`_.

2.0.0 (2017-11-05)
==================

- Rename ``TimestampToNormalized64BitIntNormalizer`` to
  ``TimestampTo64BitIntNormalizer`` for consistency.
- Make ``TimestampTo64BitIntNormalizer`` subclass
  ``TimestampNormalizer`` for simplicity.
- Rename ``FloatToNormalized64BitIntNormalizer`` to
  ``PersistentFloatTo64BitIntNormalizer`` for consistency and to
  reflect its purpose.
- Make ``PersistentFloatTo64BitIntNormalizer`` subclass
  ``FloatTo64BitIntNormalizer``.
- Add ``IDeferredCatalog`` and an implementation in
  ``DeferredCatalog`` to allow creating catalog objects that don't
  participate in event subscription-based indexing. This replaces
  ``IMetadataIndex``, which is now an alias for this object. See
  `issue 3 <https://github.com/NextThought/nti.zope_catalog/pull/3>`_.

1.0.0 (2017-06-15)
==================

- First PyPI release.
- Add support for Python 3.
- ``TimestampNormalizer`` also normalizes incoming datetime objects.
- Fix extent-based queries for NormalizedKeywordIndex.
- 100% test coverage.
