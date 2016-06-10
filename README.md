# Oakkeeper

CLI to set branch protection of a Github respository in a Zalando-compliant way.

[![](https://travis-ci.org/zalando-incubator/oakkeeper.svg?branch=master)](https://travis-ci.org/zalando-incubator/oakkeeper)
[![Coverage Status](https://coveralls.io/repos/github/zalando-incubator/oakkeeper/badge.svg?branch=master)](https://coveralls.io/github/zalando-incubator/oakkeeper?branch=master)

![Oakkeeper](oathkeeper.jpg)

It makes sure that for any repository:

1. The default branch is protected
2. Enforcement level is set to `everyone` (includes admins)
3. [Zappr](https://github.com/zalando/zappr) is a required status check

## Installation

    pip3 install --upgrade oakkeeper

## Usage

If you just type `oakkeeper`, it will prompt for the Github API Base URL (defaults to Github.com) and the access token to use. **Be aware that the token needs `repo` scope!** Afterwards it will read all repositories you have access to and asks to enable branch protection.

Alternatively you can provide the repository patterns as a space-separated list like so:

    oakkeeper zalando-stups/yourturn zalando/.*

## Options

* Access token: `--token` or environment variable `OK_TOKEN`. Needs `repo` scope.
* Github Url: `--base-url` or environment variable `OK_BASE_URL`. For Github Enterprise this is `<github enterprise url>/api/v3`.
* "Yes to all": `--yes` or environment variable `OK_YES`

You can also directly upload a local `.zappr.yaml` or an issue/PR template to every repository:

* Path to `.zappr.yaml`: `--zappr-path` or `OK_ZAPPR_PATH`
* Path to `ISSUE_TEMPLATE.md`: `--issue-template-path` or `OK_ISSUE_TEMPLATE_PATH`
* Path to `PULL_REQUEST_TEMPLATE.md`: `--pr-template-path` or `OK_PULL_REQUEST_TEMPLATE_PATH`
* Upload type: `--upload-type` or `OK_UPLOAD_TYPE`. Might be `commit` (commit to default branch) or `pr` (open pull request).

## License

Apache 2, see [LICENSE](LICENSE.txt).
