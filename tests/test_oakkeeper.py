from nose.tools import with_setup
from unittest.mock import MagicMock
from click.testing import CliRunner
from oakkeeper.cli import main
import oakkeeper.api as api

GITHUB_API = 'https://github.api'
TOKEN = '123'
REPO_DATA = {
    'default_branch': 'release',
    'full_name': 'foo/bar'
}


def setup():
    api.get_repos_page_count = MagicMock(return_value=1)
    api.get_repos = MagicMock(return_value=[REPO_DATA])


def teardown():
    try:
        api.get_repos.reset_mock()
        api.protect_branch.reset_mock()
        api.ensure_branch_protection.reset_mock()
        api.get_branch_data.reset_mock()
        api.get_repos_page_count.reset_mock()
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
    result = runner.invoke(main, [
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
    result = runner.invoke(main, [
        'foo/bar',
        '--base-url',
        GITHUB_API,
        '--token',
        TOKEN,
        '--yes'
    ])
    assert 0 == result.exit_code
    api.protect_branch.assert_called_with(GITHUB_API, TOKEN, 'foo/bar', 'release', ['zappr'])
    api.get_branch_data.assert_called_with(GITHUB_API, TOKEN, 'foo/bar', 'release')
