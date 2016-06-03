import click
from clickclick import Action
import oakkeeper.api as api


@click.command()
@click.argument('repos', nargs=-1, help='A space separated list of repositories where you want to enable branch protection')
@click.option('--base-url', prompt='Github API Base URL', default='https://api.github.com', help='The Github API ase URL - change the default if you use Github Enterprise')
@click.option('--token', prompt='Your personal access token', hide_input=True, help='A personal access token of yours with "repo" scope')
@click.option('-y', is_flag=True, default=False, help="If enabled, does not ask for confirmation")
def main(repos, base_url, token, y):
    if len(repos) > 0:
        # enable only for these repos
        for repo in repos:
            try:
                with Action('Protecting branches for {repo}'.format(repo=repo)):
                    api.protect_branch(base_url, token, repo)
            except Exception as e:
                # handled already by Action
                pass
    else:
        page = 0
        page_total = api.get_repos_page_count(base_url, token)
        while page <= page_total:
            repos = api.get_repos(base_url, token, page)
            for repo in repos:
                repo_name = repo['full_name']
                default_branch = repo['default_branch']
                protect = y
                if not y:
                    protect = click.confirm('Protect {repo}?'.format(repo=repo_name))
                if protect:
                    try:
                        with Action('Protecting branches for {repo}'.format(repo=repo_name)):
                            api.protect_branch(base_url, token, repo_name, default_branch)
                    except Exception as e:
                        # handled already by Action
                        pass
            page += 1
