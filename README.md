# Oakkeeper

Swears to protect your branches.

![Oakkeeper](oathkeeper.jpg)

It makes sure that for any repository:

1. The default branch is protected
2. Enforcement level is set to `everyone` (includes admins)
3. [Zappr](https://github.com/zalando/zappr) is a required status check

## Installation

    pip3 install --upgrade oakkeeper

## Usage

If you just type `oakkeeper`, it will prompt for the Github API Base URL (defaults to Github.com) and the access token to use. **Be aware that the token needs `repo` scope!** Afterwards it will read all repositories you have access to and asks to enable branch protection.

Alternatively you can provide the repositories as a space-separated list like so:

    oakkeeper zalando-stups/yourturn zalando-incubator/fahrschein zalando/zmon

* Access token: `--token` or environment variable `OK_TOKEN`
* Github Url: `--base-url` or environment variable `OK_BASE_URL`
* "Yes to all": `-y` or environment variable `OK_Y`

