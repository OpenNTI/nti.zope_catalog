=========
 Changes
=========

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
