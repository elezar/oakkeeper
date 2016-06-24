import importlib
from nose.tools import with_setup
from unittest.mock import MagicMock
from unittest.mock import patch
from click.testing import CliRunner
from oakkeeper.cli import main
from oakkeeper import cli
from oakkeeper import api


GITHUB_API = 'https://github.api'
TOKEN = '123'
REPO_DATA = {
    'default_branch': 'release',
    'full_name': 'foo/bar'
}


def setup():
    api.get_repos_page_count = MagicMock(return_value=0)
    api.get_repos = MagicMock(return_value=[REPO_DATA])


# FIXME: huge hack to not break old tests
def teardown():
    importlib.reload(api)


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


@with_setup(setup, teardown)
def test_upload():
    api.commit_files = MagicMock()
    runner = CliRunner()
    TEST_FILES = {
        '.zappr.yaml': 'approvals\n  minimum: 2\n',
        '.github/PULL_REQUEST_TEMPLATE.md': '# PULL REQUEST',
        '.github/ISSUE_TEMPLATE.md': '# ISSUE'
    }
    with runner.isolated_filesystem():
        with open('PR.md', 'w') as f:
            f.write(TEST_FILES['.github/PULL_REQUEST_TEMPLATE.md'])
        with open('ISSUE.md', 'w') as f:
            f.write(TEST_FILES['.github/ISSUE_TEMPLATE.md'])
        with open('.zappr.yaml', 'w') as f:
            f.write(TEST_FILES['.zappr.yaml'])
        result = runner.invoke(main, [
            'foo/bar',
            '--base-url', GITHUB_API,
            '-T', TOKEN,
            '--upload-type', 'commit',
            '--pr-template-path', 'PR.md',
            '--issue-template-path', 'ISSUE.md',
            '--zappr-path', '.zappr.yaml',
            '--yes'
        ], catch_exceptions=False)
        assert result.exit_code == 0
        api.commit_files.assert_called_with(
            base_url=GITHUB_API,
            token=TOKEN,
            repo=REPO_DATA['full_name'],
            branch_name=REPO_DATA['default_branch'],
            files=TEST_FILES
        )


def test_patterns_argument():
    with patch.object(api, 'get_repos_page_count') as get_repos_page_count, \
            patch.object(api, 'get_repos') as get_repos, \
            patch.object(cli, 'protect_repo') as protect_repo:
        matching, not_matching = dict(full_name='bar'), dict(full_name='foo')

        get_repos_page_count.return_value = 0
        get_repos.return_value = (not_matching, matching)

        runner = CliRunner()
        result = runner.invoke(main, [
            '--yes',
            '--base-url',
            GITHUB_API,
            '--token',
            TOKEN,
            '^b.*$'
        ])

        assert 0 == result.exit_code
        protect_repo.assert_called_once_with(base_url=GITHUB_API,
                                             token=TOKEN,
                                             repo_data=matching,
                                             files=dict(),
                                             upload_type='commit')


@with_setup(setup, teardown)
def test_push_to_protected_branch():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with patch.object(api, 'commit_files') as commit_files, patch.object(api, 'ensure_branch_protection'):
            commit_files.side_effect = api.StatusCheckError()

            with open('.zappr.yaml', 'w') as f:
                f.write('''approvals:\n    minimum: 2\n''')

            result = runner.invoke(main, [
                '--base-url', GITHUB_API,
                '--token', TOKEN,
                '--zappr-path', '.zappr.yaml',
                '--yes',
                '^foo/bar$'
            ])

            assert 0 == result.exit_code
            assert 'EXCEPTION' not in result.output
            assert 'Unable to commit files to foo/bar: status checks failed' in result.output


@with_setup(setup, teardown)
def test_create_pr_branch_exists():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with patch.object(api, 'submit_pr') as submit_pr, patch.object(api, 'ensure_branch_protection'):
            submit_pr.side_effect = api.BranchAlreadyExistsError('oakkeeper-add-files')

            with open('.zappr.yaml', 'w') as f:
                f.write('''approvals:\n    minimum: 2\n''')

            result = runner.invoke(main, [
                '--base-url', GITHUB_API,
                '--token', TOKEN,
                '--zappr-path', '.zappr.yaml',
                '--upload-type', 'pr',
                '--yes',
                '^foo/bar$'
            ])

            assert 0 == result.exit_code
            assert 'EXCEPTION' not in result.output
            assert "Unable to commit files to foo/bar: branch 'oakkeeper-add-files' already exists" in result.output
