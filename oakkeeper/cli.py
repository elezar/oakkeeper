import re
import click
import oakkeeper
import oakkeeper.api as api
from clickclick import Action, info


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('Oakkeeper {}'.format(oakkeeper.__version__))
    ctx.exit()


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('patterns',
                nargs=-1)
@click.option('--base-url',
              '-U',
              envvar='OK_BASE_URL',
              prompt='Github API Base URL',
              default='https://api.github.com',
              help='The Github API Base URL. For GHE use <GHE URL>/api/v3.')
@click.option('--token',
              '-T',
              envvar='OK_TOKEN',
              prompt='Your personal access token',
              hide_input=True,
              help='Your personal access token to use, must have "repo" scope.')
@click.option('--yes',
              '-Y',
              envvar='OK_YES',
              is_flag=True,
              default=False,
              help='Do not prompt for every repository, protect branches everywhere.')
@click.option('--zappr-path',
              '-P',
              envvar='OK_ZAPPR_PATH',
              type=click.Path(),
              help='Path to .zappr.yaml that should be put into repositories. Leave empty to add .zappy.yaml.')
@click.option('--zappr-upload-type',
              '-Z',
              envvar='OK_ZAPPR_UPLOAD_TYPE',
              default='commit',
              type=click.Choice(['commit', 'pr']),
              help='How to put .zappr.yaml into the repositories: Either via master commit ("commit") or pull request ("pr").')
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
def main(patterns, base_url, token, yes, zappr_path, zappr_upload_type, dry_run):
    """
    oakkeeper my-org/.* --zappr-path ~/default-zappr.yaml
    """
    zappr_config = None
    if zappr_path:
        with open(zappr_path, 'r') as zappr_config_file:
            zappr_config = zappr_config_file.read()
    repos = []
    with Action('Collecting repositories...') as action:
        for repo_data in get_repositories(base_url, token, patterns):
            repos.append(repo_data)
            action.progress()
    for repo_data in repos:
        if dry_run:
            info(repo_data['full_name'])
        else:
            protect = yes
            if not yes:
                protect = click.confirm('Protect {repo}?'.format(repo=repo_data['full_name']))
            if protect:
                protect_repo(base_url=base_url, token=token, repo_data=repo_data,
                             zappr_config=zappr_config, zappr_upload_type=zappr_upload_type)


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


def protect_repo(base_url, token, repo_data, zappr_config, zappr_upload_type):
    repo_name = repo_data['full_name']
    default_branch = repo_data['default_branch']
    try:
        if zappr_config is not None:
            with Action('Uploading .zappr.yaml for {repo}'.format(repo=repo_name)):
                api.upload_file(base_url=base_url, token=token, repo=repo_name,
                                default_branch=default_branch, file_content=zappr_config,
                                upload_type=zappr_upload_type)
        with Action('Protecting branches for {repo}'.format(repo=repo_name)):
            api.ensure_branch_protection(base_url=base_url, token=token, repo=repo_name,
                                         branch=default_branch)
    except:
        # handled already by Action
        pass
