=========
 Changes
=========

2.0.0 (unreleased)
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


1.0.0 (2017-06-15)
==================

- First PyPI release.
- Add support for Python 3.
- ``TimestampNormalizer`` also normalizes incoming datetime objects.
- Fix extent-based queries for NormalizedKeywordIndex.
- 100% test coverage.
