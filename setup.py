import os
import sys
import inspect
from setuptools import setup
from setuptools.command.test import test as TestCommand

__location__ = os.path.join(os.getcwd(), os.path.dirname(inspect.getfile(inspect.currentframe())))


def read_version(package):
    with open(os.path.join(package, '__init__.py'), 'r') as fd:
        for line in fd:
            if line.startswith('__version__ = '):
                return line.split()[-1].strip().strip("'")


def get_install_requirements(path):
    content = open(os.path.join(__location__, path)).read()
    return [req for req in content.split('\\n') if req != '']


def read(fname):
    return open(os.path.join(__location__, fname)).read()


class PyTest(TestCommand):
    user_options = [('cov-html=', None, 'Generate junit html report')]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.cov = None
        self.pytest_args = ['--cov', 'oakkeeper', '--cov-report', 'term-missing']
        self.cov_html = False

    def finalize_options(self):
        TestCommand.finalize_options(self)
        if self.cov_html:
            self.pytest_args.extend(['--cov-report', 'html'])

    def run_tests(self):
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


VERSION = read_version('oakkeeper')

config = {
    'description': 'CLI to set branch protection of a Github repository in a Zalando-compliant way',
    'author': 'Nikolaus Piccolotto',
    'author_email': 'nikolaus.piccolotto@zalando.de',
    'url': 'https://github.com/zalando-incubator/oakkeeper',
    'download_url': 'https://github.com/zalando-incubator/oakkeeper/tarball/{version}'.format(version=VERSION),
    'version': VERSION,
    'cmdclass': {'test': PyTest},
    'test_suite': 'tests',
    'tests_require': ['nose', 'pytest-cov', 'pytest'],
    'install_requires': get_install_requirements('requirements.txt'),
    'packages': [
        'oakkeeper'
    ],
    'scripts': [],
    'name': 'oakkeeper',
    'entry_points': {
        'console_scripts': ['oakkeeper = oakkeeper.cli:main']}
}

setup(**config)
