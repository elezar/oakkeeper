from nose.tools import *
from unittest.mock import MagicMock
from click.testing import CliRunner
from oakkeeper.cli import oakkeeper
import oakkeeper.api as api

GITHUB_API = 'https://github.api'
TOKEN = '123'
REPO_DATA = {
    'default_branch': 'release'
}

def setup():
    api.get_repo = MagicMock(return_value=REPO_DATA)


def teardown():
    try:
        api.get_repo.reset_mock()
        api.protect_branch.reset_mock()
        api.ensure_branch_protection.reset_mock()
        api.get_branch_data.reset_mock()
    except:
        pass


@with_setup(setup, teardown)
def test_nothing_to_do():
    branch_data = {
        'protection': {
            'required_status_checks': {
                'contexts': ['zappr']
            }
        }
    }
    api.get_branch_data = MagicMock(return_value=branch_data)
    api.protect_branch = MagicMock()
    runner = CliRunner()
    result = runner.invoke(oakkeeper, [
        'foo/bar',
        '--base-url',
        GITHUB_API,
        '--token',
        TOKEN
    ])
    assert 0 == result.exit_code
    api.protect_branch.assert_not_called()


@with_setup(setup, teardown)
def test_happy_case():
    # ['protection']['required_status_checks']['contexts']
    branch_data = {
        'protection': {
            'required_status_checks': {
                'contexts': []
            }
        }
    }
    api.get_branch_data = MagicMock(return_value=branch_data)
    api.protect_branch = MagicMock(return_value=None)
    runner = CliRunner()
    result = runner.invoke(oakkeeper, [
        'foo/bar',
        '--base-url',
        GITHUB_API,
        '--token',
        TOKEN
    ])
    assert 0 == result.exit_code
    api.protect_branch.assert_called_with(GITHUB_API, TOKEN, 'foo/bar', 'release', ['zappr'])
    api.get_branch_data.assert_called_with(GITHUB_API, TOKEN, 'foo/bar', 'release')


@with_setup(setup, teardown)
def test_no_access():
    runner = CliRunner()
    api.get_repo = MagicMock(side_effect=Exception)
    api.protect_branch = MagicMock(return_value=None)
    result = runner.invoke(oakkeeper, [
        'foo/bar',
        '--base-url',
        GITHUB_API,
        '--token',
        TOKEN
    ])
    print(result.output)
    assert 0 == result.exit_code
    assert 'EXCEPTION OCCURRED' in result.output
    api.protect_branch.assert_not_called()
