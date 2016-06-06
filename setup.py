try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'CLI to set branch protection of a Github respository in a Zalando-compliant way',
    'author': 'Nikolaus Piccolotto',
    'url': 'https://github.com/zalando-incubator/oakkeeper',
    'download_url': 'https://github.com/zalando-incubator/oakkeeper/tarball/0.2',
    'author_email': 'nikolaus.piccolotto@zalando.de',
    'version': '0.2',
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
    'entry_points': {'console_scripts': ['oakkeeper = oakkeeper.cli:oakkeeper']}
}

setup(**config)
