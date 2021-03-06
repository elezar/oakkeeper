import importlib
from nose.tools import with_setup
from unittest.mock import MagicMock, patch
from click.testing import CliRunner
from oakkeeper.cli import main
from oakkeeper import cli, api, zappr

GITHUB_API = 'https://github.api'
ZAPPR_API = 'https://zappr.api'
TOKEN = '123'
REPO_DATA = {
    'id': 1,
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
            patch.object(cli, 'update_repo') as update_repo:
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
        update_repo.assert_called_once_with(base_url=GITHUB_API,
                                            token=TOKEN,
                                            repo_data=matching,
                                            files=dict(),
                                            upload_type='commit')


@with_setup(setup, teardown)
def test_push_to_protected_branch():
    runner = CliRunner()
    with runner.isolated_filesystem():
        with patch.object(api, 'commit_files') as commit_files:
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
        with patch.object(api, 'submit_pr') as submit_pr:
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


@with_setup(setup, teardown)
@patch('oakkeeper.zappr.enable_check')
@patch('oakkeeper.zappr.disable_check')
def test_apply_checks(disable_check, enable_check):
    runner = CliRunner()
    result = runner.invoke(main, [
        '--base-url', GITHUB_API,
        '--zappr-base-url', ZAPPR_API,
        '--token', TOKEN,
        '--enable', 'approval',
        '--disable', 'commitmessage',
        '--yes',
        'foo/bar'
    ])
    assert result.exit_code == 0
    assert 'EXCEPTION' not in result.output
    enable_check.assert_called_once_with(base_url=ZAPPR_API, repository_id=1, check='approval', token=TOKEN)
    disable_check.assert_called_once_with(base_url=ZAPPR_API, repository_id=1, check='commitmessage', token=TOKEN)


@with_setup(setup, teardown)
@patch('oakkeeper.zappr.enable_check')
@patch('oakkeeper.zappr.disable_check')
def test_check_error_message(disable_check, enable_check):
    enable_check.side_effect = zappr.ZapprException({'title': 'Error', 'detail': 'Already exists'})
    disable_check.side_effect = zappr.ZapprException({'title': 'Error', 'detail': 'Not gonna happen'})
    runner = CliRunner()
    result = runner.invoke(main, [
        '--base-url', GITHUB_API,
        '--zappr-base-url', ZAPPR_API,
        '--token', TOKEN,
        '--enable', 'approval',
        '--disable', 'commitmessage',
        '--yes',
        'foo/bar'
    ])
    assert result.exit_code == 0
    assert 'EXCEPTION' not in result.output
    enable_check.assert_called_once_with(base_url=ZAPPR_API, repository_id=1, check='approval', token=TOKEN)
    disable_check.assert_called_once_with(base_url=ZAPPR_API, repository_id=1, check='commitmessage', token=TOKEN)
    assert "Could not enable approval: Error: Already exists" in result.output
    assert "Could not disable commitmessage: Error: Not gonna happen" in result.output
