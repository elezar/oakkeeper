import re
import json
import base64
import requests
from requests.auth import HTTPBasicAuth

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


def get_repo(base_url, token, repo):
    auth = HTTPBasicAuth('token', token)
    url = base_url + '/repos/{repo}'.format(repo=repo)
    r = requests.get(url, auth=auth)
    r.raise_for_status()
    return r.json()


def get_repos(base_url, token, page=0):
    url = base_url + '/user/repos?visibility=public&page={page}'.format(page=page)
    auth = HTTPBasicAuth('token', token)
    r = requests.get(url, auth=auth)
    r.raise_for_status()
    return r.json()


def get_branch_data(base_url, token, repo, branch):
    url = base_url + '/repos/{repo}/branches/{branch}'.format(repo=repo, branch=branch)
    headers = {'Accept': 'application/vnd.github.loki-preview+json'}
    auth = HTTPBasicAuth('token', token)
    r = requests.get(url, headers=headers, auth=auth)
    r.raise_for_status()
    return r.json()


def protect_branch(base_url, token, repo, branch, required_contexts):
    protection_payload = {
        'protection': {
            'enabled': True,
            'required_status_checks': {
                'enforcement_level': 'everyone',
                'contexts': required_contexts
            }
        }
    }
    url = base_url + '/repos/{repo}/branches/{branch}'.format(repo=repo, branch=branch)
    headers = {'Accept': 'application/vnd.github.loki-preview+json'}
    auth = HTTPBasicAuth('token', token)
    r = requests.patch(
        url,
        headers=headers,
        auth=auth,
        data=json.dumps(protection_payload))
    r.raise_for_status()


def ensure_branch_protection(base_url, token, repo, branch='master'):
    branch_data = get_branch_data(base_url, token, repo, branch)
    contexts = branch_data['protection']['required_status_checks']['contexts']
    if 'zappr' not in contexts:
        contexts.append('zappr')
        protect_branch(base_url, token, repo, branch, contexts)


def get_commits(base_url, token, repo):
    url = base_url + '/repos/{repo}/commits'.format(repo=repo)
    auth = HTTPBasicAuth('token', token)
    r = requests.get(url, auth=auth)
    r.raise_for_status()
    return r.json()


def create_branch(base_url, token, repo, branch_name, from_sha):
    url = base_url + '/repos/{repo}/git/refs'.format(repo=repo)
    auth = HTTPBasicAuth('token', token)
    payload = {
        'ref': 'refs/heads/{name}'.format(name=branch_name),
        'sha': from_sha
    }
    r = requests.post(url, data=json.dumps(payload), auth=auth)
    r.raise_for_status()
    return r.json()


def create_pr(base_url, token, repo, base, head, title='Add .zappr.yaml', body=''):
    url = base_url + '/repos/{repo}/pulls'.format(repo=repo)
    auth = HTTPBasicAuth('token', token)
    payload = {
        'title': title,
        'head': head,
        'base': base,
        'content': body
    }
    r = requests.post(url, auth=auth, data=json.dumps(payload))
    r.raise_for_status()
    return None


def commit_file(base_url, token, repo, branch_name, file_name, file_content):
    url = base_url + '/repos/{repo}/contents/{file_name}'.format(repo=repo, file_name=file_name)
    auth = HTTPBasicAuth('token', token)
    read = requests.get(url + '?ref={branch}'.format(branch=branch_name), auth=auth)
    sha = read.json()['sha'] if read.ok else None
    payload = {
        'message': 'Add .zappr.yaml',
        'content': base64.b64encode(file_content.encode('UTF-8')).decode('ascii'),
        'branch': branch_name
    }
    if sha:
        payload['sha'] = sha
    r = requests.put(
        url,
        auth=auth,
        data=json.dumps(payload)
    )
    r.raise_for_status()
    return r.json()


def upload_file(base_url, token, repo, default_branch, file_content, upload_type, file_name='.zappr.yaml',
                branch_name='add-zappr-yaml'):
    if upload_type == 'commit':
        commit_file(base_url=base_url, token=token, repo=repo, branch_name=default_branch, file_name=file_name,
                    file_content=file_content)
    elif upload_type == 'pr':
        commits = get_commits(base_url=base_url, token=token, repo=repo)
        head = commits[0]['sha']
        create_branch(base_url=base_url, token=token, repo=repo, branch_name=branch_name, from_sha=head)
        commit_resp = commit_file(base_url=base_url, token=token, repo=repo, branch_name=branch_name,
                                  file_name=file_name, file_content=file_content)
        create_pr(base_url=base_url, token=token, repo=repo, base=default_branch, head=commit_resp['commit']['sha'])
    else:
        return None
