import re
import click
import oakkeeper
import oakkeeper.api as api
import oakkeeper.zappr as zappr_api
from clickclick import Action, info


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('Oakkeeper {}'.format(oakkeeper.__version__))
    ctx.exit()


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
ZAPPR_CHECKS = ['approval', 'commitmessage', 'autobranch', 'specification', 'pullrequestlabels']


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('patterns', nargs=-1)
@click.option('--base-url',
              '-U',
              envvar='OK_BASE_URL',
              prompt='Github API Base URL',
              default='https://api.github.com',
              help='The Github API Base URL. For GHE use <GHE URL>/api/v3.')
@click.option('--yes',
              '-Y',
              envvar='OK_YES',
              is_flag=True,
              default=False,
              help='Do not prompt for every repository.')
@click.option('--zappr-base-url',
              envvar='OK_ZAPPR_BASE_URL',
              prompt='Zappr Base URL',
              default='https://zappr.opensource.zalan.do',
              help='URL to Zappr, defaults to Zappr Opensource.')
@click.option('--enable',
              '-E',
              envvar='OK_ZAPPR_ENABLE_CHECKS',
              type=click.Choice(ZAPPR_CHECKS),
              multiple=True,
              help='Checks you want to enable for a repository.')
@click.option('--disable',
              '-D',
              envvar='OK_ZAPPR_DISABLE_CHECKS',
              type=click.Choice(ZAPPR_CHECKS),
              multiple=True,
              help='Checks you want to disable for a repository.')
@click.option('--zappr-path',
              '-Z',
              envvar='OK_ZAPPR_PATH',
              type=click.Path(),
              help='Path to .zappr.yaml that should be put into repositories.')
@click.option('--pr-template-path',
              '-PR',
              envvar='OK_PR_TEMPLATE_PATH',
              help='Path to pull request template that should be put into repositories.')
@click.option('--issue-template-path',
              '-I',
              envvar='OK_ISSUE_TEMPLATE_PATH',
              help='Path to issue template that should be put into repositories.')
@click.option('--upload-type',
              '-UT',
              envvar='OK_UPLOAD_TYPE',
              default='commit',
              type=click.Choice(['commit', 'pr']),
              help='How to put files into the repositories: Either via master commit ("commit") or '
                   'pull request ("pr").')
@click.option('--token',
              '-T',
              envvar='OK_TOKEN',
              prompt='Your personal access token',
              hide_input=True,
              help='Your personal access token to use, must have "repo" scope. ' +
                   'In case you want to manage Zappr checks it also needs "admin:repo_hook" and you must have admin '
                   'access to the repository.')
@click.option('--version',
              '-V',
              is_flag=True,
              callback=print_version,
              expose_value=False,
              is_eager=True,
              help='Print the current version number and exit.')
@click.option('--dry-run',
              is_flag=True,
              default=False,
              help='Print affected repositories and do nothing')
def main(patterns, base_url, yes, zappr_base_url, enable, disable, zappr_path, pr_template_path,
         issue_template_path, upload_type, token, dry_run):
    """
    oakkeeper my-org/.* --zappr-path ~/default-zappr.yaml
    """
    files = {}
    if zappr_path:
        with open(zappr_path, 'r') as zappr_config_file:
            files['.zappr.yaml'] = zappr_config_file.read()
    if pr_template_path:
        with open(pr_template_path, 'r') as pr_template_file:
            files['.github/PULL_REQUEST_TEMPLATE.md'] = pr_template_file.read()
    if issue_template_path:
        with open(issue_template_path, 'r') as issue_template_file:
            files['.github/ISSUE_TEMPLATE.md'] = issue_template_file.read()

    repos = []
    with Action('Collecting repositories...') as action:
        for repo_data in get_repositories(base_url, token, patterns):
            repos.append(repo_data)
            action.progress()
    for repo_data in repos:
        if dry_run:
            info(repo_data['full_name'])
        else:
            do_update = yes
            if not yes:
                do_update = click.confirm('Update {repo}?'.format(repo=repo_data['full_name']))
            if do_update:
                update_repo(base_url=base_url, token=token, repo_data=repo_data,
                            files=files, upload_type=upload_type)
                if len(enable) > 0 or len(disable) > 0:
                    apply_zappr_checks(zappr_base_url=zappr_base_url, token=token, repo_data=repo_data,
                                       enable_checks=enable, disable_checks=disable)


def get_repositories(base_url, token, patterns):
    page = 0
    page_total = api.get_repos_page_count(base_url, token)
    while page <= page_total:
        repositories = api.get_repos(base_url, token, page)
        for repo_data in repositories:
            for pattern in patterns:
                if re.match(pattern, repo_data['full_name']):
                    yield repo_data
                    break
        page += 1


def apply_zappr_checks(zappr_base_url, repo_data, enable_checks, disable_checks, token):
    repo_id = repo_data['id']
    repo_name = repo_data['full_name']
    try:
        for check in enable_checks:
            with Action('Enabling check {check} for {repo}'.format(check=check, repo=repo_name)) as action:
                try:
                    zappr_api.enable_check(base_url=zappr_base_url, repository_id=repo_id, check=check, token=token)
                except zappr_api.ZapprException as e:
                    action.warning('\nCould not enable {check}: {error}'.format(check=check, error=e))
        for check in disable_checks:
            with Action('Disabling check {check} for {repo}'.format(check=check, repo=repo_name)) as action:
                try:
                    zappr_api.disable_check(base_url=zappr_base_url, repository_id=repo_id, check=check, token=token)
                except zappr_api.ZapprException as e:
                    action.warning('\nCould not disable {check}: {error}'.format(check=check, error=e))
    except:
        pass


def update_repo(base_url, token, repo_data, files, upload_type):
    repo_name = repo_data['full_name']
    default_branch = repo_data['default_branch']
    try:
        if len(files) > 0:
            with Action('Uploading files for {repo}'.format(repo=repo_name)) as action:
                if upload_type == 'commit':
                    try:
                        api.commit_files(base_url=base_url, token=token, repo=repo_name, branch_name=default_branch,
                                         files=files)
                    except api.StatusCheckError:
                        action.warning('\nUnable to commit files to {}: status checks failed'.format(repo_name))
                elif upload_type == 'pr':
                    pr_title = 'Add ' + ', '.join(list(files.keys()))
                    branch_name = 'oakkeeper-add-files'
                    try:
                        api.submit_pr(base_url=base_url, token=token, repo=repo_name, default_branch=default_branch,
                                      branch_name=branch_name, title=pr_title, files=files)
                    except api.BranchAlreadyExistsError:
                        action.warning('''\nUnable to commit files to {}: branch '{}' already exists'''.format(
                            repo_name, branch_name))
    except:
        # handled already by Action
        pass
