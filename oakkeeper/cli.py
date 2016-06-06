import click
import oakkeeper
import oakkeeper.api as api
from clickclick import Action


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('Oakkeper {}'.format(oakkeeper.__version__))
    ctx.exit()


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('repositories',
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
              envvar='OK_Y',
              is_flag=True,
              default=False,
              help='Do not prompt for every repository, protect branches everywhere.')
@click.option('--version',
              '-V',
              is_flag=True,
              callback=print_version,
              expose_value=False,
              is_eager=True,
              help='Print the current version number and exit.')
def oakkeeper(repositories, base_url, token, y):
    if len(repositories) > 0:
        # enable only for these repos
        for repo in repositories:
            try:
                with Action('Protecting branches for {repo}'.format(repo=repo)):
                    repo_data = api.get_repo(base_url, token, repo)
                    api.ensure_branch_protection(base_url, token, repo, repo_data['default_branch'])
            except Exception as e:
                # handled already by Action
                pass
    else:
        page = 0
        page_total = api.get_repos_page_count(base_url, token)
        while page <= page_total:
            repositories = api.get_repos(base_url, token, page)
            for repo in repositories:
                repo_name = repo['full_name']
                default_branch = repo['default_branch']
                protect = y
                if not y:
                    protect = click.confirm('Protect {repo}?'.format(repo=repo_name))
                if protect:
                    try:
                        with Action('Protecting branches for {repo}'.format(repo=repo_name)):
                            api.ensure_branch_protection(base_url, token, repo_name, default_branch)
                    except Exception as e:
                        # handled already by Action
                        pass
            page += 1
