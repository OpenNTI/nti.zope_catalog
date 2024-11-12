import codecs
from setuptools import setup
from setuptools import find_namespace_packages


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
        'Programming Language :: Python :: 3',
        "Programming Language :: Python :: 3 :: Only",
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    url="https://github.com/OpenNTI/nti.zope_catalog",
    project_urls={
        'Documentation': 'https://ntizope-catalog.readthedocs.io/en/latest/',
    },
    zip_safe=True,
    packages=find_namespace_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'BTrees >= 4.8.0',
        'nti.property >= 1.0.0',
        'nti.zodb >= 1.0.0',
        'persistent',
        'pytz',
        'six',
        'zc.catalog >= 2.0.1',
        'ZODB >= 5.0.0',
        'zope.cachedescriptors',
        'zope.catalog',
        'zope.component',
        'zope.container',
        'zope.index',
        'zope.interface',
        'zope.location',
    ],
    extras_require={
        'test': TESTS_REQUIRE,
        'docs': [
            'Sphinx',
            'repoze.sphinx.autointerface',
            'sphinx_rtd_theme',
        ],
    },
    python_requires=">=3.10",
)
