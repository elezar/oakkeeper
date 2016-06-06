try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

config = {
    'description': 'CLI to configure Zappr in a compliant way',
    'author': 'Nikolaus Piccolotto',
    'url': 'https://github.bus.zalan.do/torch/oakkeeper',
    'download_url': 'Where to download it.',
    'author_email': 'nikolaus.piccolotto@zalando.de',
    'version': '0.1',
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
    'name': 'oakkeeper'
}

setup(**config)
