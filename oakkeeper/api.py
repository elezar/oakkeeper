import re
import json
import base64
import requests
from requests.auth import HTTPBasicAuth

PAGE_REGEX = re.compile(r'page=([0-9]+)')


class ApiError(BaseException):
    pass


class StatusCheckError(ApiError):
    """
    Raised when commit doesn't pass required status checks
    """


class BranchAlreadyExistsError(ApiError):
    def __init__(self, branch_name):
        super().__init__("branch '{}' already exists".format(branch_name))


def get_repos_page_count(base_url, token):
    url = base_url + '/user/repos?visibility=public'
    auth = HTTPBasicAuth('token', token)
    r = requests.get(url, auth=auth)
    r.raise_for_status()
    # '<https://api.github.com/user/repos?page=2>; rel="next", <https://api.github.com/user/repos?page=11>; rel="last"'
    try:
        link_header = r.headers['Link']
        return int(PAGE_REGEX.split(link_header)[3])
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
    if r.status_code == 422 and 'Reference already exists' in r.text:
        raise BranchAlreadyExistsError(branch_name)
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


def commit_files(base_url, token, repo, branch_name, files):
    result = []
    for file_path, file_content in files.items():
        commit = commit_file(base_url=base_url, token=token, repo=repo, branch_name=branch_name, file_path=file_path,
                             file_content=file_content)
        result.append({'file': file_path, 'commit': commit})
    return result


def commit_file(base_url, token, repo, branch_name, file_path, file_content):
    url = base_url + '/repos/{repo}/contents/{file_path}'.format(repo=repo, file_path=file_path)
    auth = HTTPBasicAuth('token', token)
    read = requests.get(url + '?ref={branch}'.format(branch=branch_name), auth=auth)
    sha = read.json()['sha'] if read.ok else None
    payload = {
        'message': 'Add {file_path}'.format(file_path=file_path),
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
    if r.status_code == 409 and 'Required status check' in r.text:
        raise StatusCheckError()
    r.raise_for_status()
    return r.json()


def submit_pr(base_url, token, repo, default_branch, title, branch_name, files):
    commits = get_commits(base_url=base_url, token=token, repo=repo)
    head = commits[0]['sha']
    create_branch(base_url=base_url, token=token, repo=repo, branch_name=branch_name, from_sha=head)
    commits = commit_files(base_url=base_url, token=token, repo=repo, files=files, branch_name=branch_name)
    last_commit = commits[-1]
    create_pr(base_url=base_url, token=token, repo=repo, title=title, base=default_branch,
              head=last_commit['commit']['commit']['sha'])
