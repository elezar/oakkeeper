import requests
from requests.auth import HTTPBasicAuth
import json
import re

PAGE_REGEX = re.compile(r'page=([0-9]+)')


def get_repos_page_count(base_url, token):
    url = base_url + '/user/repos?visibility=public'
    auth = HTTPBasicAuth('token', token)
    r = requests.get(url, auth=auth)
    r.raise_for_status()
    # '<https://api.github.com/user/repos?page=2>; rel="next", <https://api.github.com/user/repos?page=11>; rel="last"'
    try:
        link_header = r.headers['Link']
        return int(PAGE_REGEX.split(link_header)[3]) - 1
    except KeyError:
        return 0


def get_repos(base_url, token, page=0):
    url = base_url + '/user/repos?visibility=public&page={page}'.format(page=page)
    auth = HTTPBasicAuth('token', token)
    r = requests.get(url, auth=auth)
    r.raise_for_status()
    return r.json()


def protect_branch(base_url, token, repo, branch='master'):
    url = base_url + '/repos/{repo}/branches/{branch}'.format(repo=repo, branch=branch)
    headers = {'Accept': 'application/vnd.github.loki-preview+json'}
    auth = HTTPBasicAuth('token', token)
    contexts = requests.get(url, headers=headers, auth=auth).json()['protection']['required_status_checks']['contexts']
    if 'zappr' not in contexts:
        contexts.append('zappr')
        protection_payload = {
            'protection': {
                'enabled': True,
                'required_status_checks': {
                    'enforcement_level': 'everyone',
                    'contexts': contexts
                }
            }
        }
        r = requests.patch(
            url,
            headers=headers,
            auth=auth,
            data=json.dumps(protection_payload))
        r.raise_for_status()
