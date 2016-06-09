import os
import subprocess
import sys

import requests
import requests.packages.urllib3
import yaml

requests.packages.urllib3.disable_warnings()


def sync_fork(repo, repo_dir, github_user):
    if 'parent' in repo:
        try:
            set_remote_upstream = 'git remote add upstream %s' % repo['parent']['ssh_url']
            subprocess.check_output(set_remote_upstream, cwd=repo_dir, shell=True)
        except:
            pass

        command_list = [
            'git checkout master',
            'git pull --rebase',
            'git merge upstream/master'
        ]
        if repo['owner']['login'] == github_user:
            command_list.append('git push origin master')
        for cmd in command_list:
            try:
                print subprocess.check_output(cmd, cwd=repo_dir, shell=True)
            except Exception as e:
                print 'failed to run command: %s' % cmd
                raise e


def update_repos(url, github_user, github_api_token, github_api_base_url,
                 enterprise_name, github_crt=None, is_team=True):
    full_url = github_api_base_url + url
    try:
        auth = (github_user, github_api_token)
        result = requests.get(full_url, auth=auth, verify=github_crt)
        data = result.json()
        if data and result.status_code < 300:
            for repo in data:
                print '--------------------------------------------------------------------------------------------'
                print repo['ssh_url']
                # print repo['owner']['login']
                pwd = subprocess.check_output('pwd').replace('\n', '')
                base_dir = "%s/%s" % (pwd, repo['owner']['login'])
                repo_dir = '%s/%s' % (base_dir, repo['name'])

                if 'PRS-UI' in repo['name']:
                    continue

                if not is_team:
                    if not os.path.exists(base_dir):
                        os.mkdir(base_dir)

                    url = github_api_base_url + '/repos/%s/%s' % (repo['owner']['login'], repo['name'])
                    repo_json = requests.get(url, auth=auth, verify=github_crt)

                    try:
                        try:
                            sync_fork(repo_json.json(), repo_dir, github_user)
                        except:
                            pass
                        branches = subprocess.check_output('git branch -a', cwd=repo_dir, shell=True)
                        if len(branches) > 0:
                            print subprocess.check_output('git up', cwd=repo_dir, shell=True)
                    except:
                        cmd = 'git clone %s' % repo['ssh_url']
                        print subprocess.check_output(cmd, cwd=base_dir, shell=True)
                else:
                    pwd = subprocess.check_output('pwd').replace('\n', '')
                    base_dir = "%s/%s" % (pwd, enterprise_name)
                    base2_dir = "%s/%s" % (base_dir, repo['owner']['login'])
                    repo_dir = '%s/%s' % (base2_dir, repo['name'])
                    try:
                        os.mkdir(base_dir)
                    except:
                        pass
                    try:
                        os.mkdir(base2_dir)
                    except:
                        pass
                    try:
                        os.mkdir(repo_dir)
                    except:
                        pass
                        # cmd = 'git clone --bare %s' % repo['ssh_url']
                        # print subprocess.check_output(cmd, cwd=base_dir, shell=True)


    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stdout)
        print 'Failed to get api request from %s' % (full_url)
        raise e


def load_config():
    with open(os.path.expanduser('~/.github-config'), 'r') as stream:
        return yaml.safe_load(stream)


def show_all_orgs(github_user, github_api_token, github_api_base_url, github_crt):
    auth = (github_user, github_api_token)
    result = requests.get(github_api_base_url + '/organizations', auth=auth, verify=github_crt)
    print github_api_base_url + '/organizations'
    data = result.json()
    for org in data:
        print org['login']
        # pprint.pprint(data)


if __name__ == '__main__':

    config = load_config()
    github_user = config['username']
    github_api_token = config['api_token']
    enterprise_host = config['enterprise_url']
    github_crt = config['enterprise_cert']
    enterprise_name = config['enterprise']
    github_api_base_url = 'https://%s/api/v3' % enterprise_host
    teams = config['teams']
    users = config['users']

    show_all_orgs(github_user, github_api_token, github_api_base_url, github_crt)

    for team in teams:
        update_repos('/orgs/%s/repos' % team, github_user,
                     github_api_token,
                     github_api_base_url,
                     enterprise_name,
                     github_crt,
                     is_team=True)

    for user in users:
        update_repos('/users/%s/repos' % user,
                     github_user,
                     github_api_token,
                     github_api_base_url,
                     enterprise_name,
                     github_crt,
                     is_team=False)
