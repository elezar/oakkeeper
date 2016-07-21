import requests
from requests.auth import AuthBase


class ZapprException(BaseException):
    def __init__(self, json):
        super().__init__('{title}: {detail}'.format(title=json['title'], detail=json['detail']))


class TokenAuth(AuthBase):
    def __init__(self, access_token):
        self.access_token = access_token

    def __call__(self, r):
        r.headers['Authorization'] = 'token ' + self.access_token
        return r


def enable_check(base_url, repository_id, check, token):
    auth = TokenAuth(token)
    url = base_url + '/api/repos/{repo}/{check}'.format(repo=repository_id, check=check)
    r = requests.put(url, auth=auth)
    if not r.ok:
        raise ZapprException(r.json())


def disable_check(base_url, repository_id, check, token):
    auth = TokenAuth(token)
    url = base_url + '/api/repos/{repo}/{check}'.format(repo=repository_id, check=check)
    r = requests.delete(url, auth=auth)
    if not r.ok:
        raise ZapprException(r.json())
