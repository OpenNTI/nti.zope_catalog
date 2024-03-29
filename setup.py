import codecs
from setuptools import setup, find_packages


TESTS_REQUIRE = [
    'pyhamcrest',
    'nti.testing',
    'zope.testing',
    'zope.testrunner',
]


def _read(fname):
    with codecs.open(fname, encoding='utf-8') as f:
        return f.read()


setup(
    name='nti.zope_catalog',
    version=_read('version.txt').strip(),
    author='Jason Madden',
    author_email='jason@nextthought.com',
    description="NTI Zope Catalog",
    long_description=(_read('README.rst') + '\n\n' + _read('CHANGES.rst')),
    license='Apache',
    keywords='Zope Catalog',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Framework :: ZODB',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    url="https://github.com/OpenNTI/nti.zope_catalog",
    zip_safe=True,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    namespace_packages=['nti'],
    tests_require=TESTS_REQUIRE,
    install_requires=[
        'setuptools',
        'BTrees >= 4.8.0',
        'nti.property >= 1.0.0',
        'nti.zodb >= 1.0.0',
        'persistent',
        'pytz',
        'six',
        'zc.catalog[stemmer] >= 2.0.1',
        'ZODB >= 5.0.0',
        'zope.cachedescriptors',
        'zope.catalog',
        'zope.component',
        'zope.container',
        'zope.index',
        'zope.interface',
        'zope.location',
        'zopyx.txng3.ext >= 4.0.0'
    ],
    extras_require={
        'test': TESTS_REQUIRE,
        'docs': [
            'Sphinx < 4', # 4 breaks autointerface == 0.8
            'repoze.sphinx.autointerface',
            'sphinx_rtd_theme',
        ],
    },
)
