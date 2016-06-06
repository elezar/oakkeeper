try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

VERSION = '0.4'

config = {
    'description': 'CLI to set branch protection of a Github respository in a Zalando-compliant way',
    'author': 'Nikolaus Piccolotto',
    'author_email': 'nikolaus.piccolotto@zalando.de',
    'url': 'https://github.com/zalando-incubator/oakkeeper',
    'download_url': 'https://github.com/zalando-incubator/oakkeeper/tarball/{version}'.format(version=VERSION),
    'version': VERSION,
    'setup_requires': [
        'nose'
    ],
    'tests_require': [
        'nose'
    ],
    'install_requires': [
        'requests',
        'click',
        'clickclick'
    ],
    'packages': [
        'oakkeeper'
    ],
    'scripts': [],
    'name': 'oakkeeper',
    'entry_points': {'console_scripts': ['oakkeeper = oakkeeper.cli:main']}
}

setup(**config)
