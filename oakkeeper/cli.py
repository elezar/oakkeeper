from clickclick import Action
import click
import oakkeeper.api as api


@click.command()
@click.argument('repositories',
                nargs=-1)
@click.option('--base-url',
              envvar='OK_BASE_URL',
              prompt='Github API Base URL',
              default='https://api.github.com')
@click.option('--token',
              envvar='OK_TOKEN',
              prompt='Your personal access token',
              hide_input=True)
@click.option('-y',
              envvar='OK_Y',
              is_flag=True,
              default=False)
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
