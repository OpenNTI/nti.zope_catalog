import codecs
from setuptools import setup, find_packages

VERSION = '0.0.0'

entry_points = {
	'console_scripts': [
	],
}

TESTS_REQUIRE = [
	'fudge',
	'nose',
	'nose-timer',
	'nose-pudb',
	'nose-progressive',
	'nose2[coverage_plugin]',
	'pyhamcrest',
	'zope.testing',
	'nti.nose_traceback_info'
]

setup(
	name='nti.zope_catalog',
	version=VERSION,
	author='Jason Madden',
	author_email='jason@nextthought.com',
	description="NTI ZODB Catalog",
	long_description=codecs.open('README.rst', encoding='utf-8').read(),
	license='Proprietary',
	keywords='ZODB Catalog',
	classifiers=[
		'Intended Audience :: Developers',
		'Natural Language :: English',
		'Operating System :: OS Independent',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.3',
		'Programming Language :: Python :: 3.4',
		'Programming Language :: Python :: Implementation :: CPython'
		'Programming Language :: Python :: Implementation :: PyPy'
	],
	packages=find_packages('src'),
	package_dir={'': 'src'},
	namespace_packages=['nti'],
	tests_require=TESTS_REQUIRE,
	install_requires=[
		'setuptools',
		'BTrees',
		'persistent',
		'pytz',
		'six',
		'zc.catalog',
		'ZODB',
		'zope.catalog',
		'zope.component',
		'zope.container',
		'zope.index',
		'zope.interface',
		'zope.security',
		'nti.property',
		'nti.zodb'
	],
	extras_require={
		'test': TESTS_REQUIRE,
	},
	entry_points=entry_points
)
