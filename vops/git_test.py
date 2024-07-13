import git
import tempfile
import os
from urllib.parse import quote


class GitParser(object):

    def __init__(self):
        self.git_user = "it.ops"
        self.git_password = 'xxxxxx'
        self.git_server = 'http://git.nextop.cc/'

    def init_repo_env(self, repoName=None):

        if not self.git_user or not repoName or not self.git_password:
            pass
        elif len(repoName.split('://')) != 2:
            pass
        else:
            if not self.git_server.startswith('http://'):
                self.git_server = 'http://' + self.git_server
            self.git_server = self.git_server.rstrip('/')
            repo_dir = tempfile.TemporaryDirectory().name
            user_passwd = ':'.join(
                [quote(self.git_user), quote(self.git_password)])
            head, git_repo = repoName.split('://')
            return [head+"://"+user_passwd+"@"+git_repo, repo_dir]

    def check_repo_isvalid(self, repoName):
        _r = self.init_repo_env(repoName)
        if _r:
            os.system('mkdir -p '+_r[1])
            try:
                git.Repo.clone_from(_r[0],_r[1])
                repo = git.Repo(_r[1])
                print(repo.active_branch)
            except Exception as e:
                logger.error()
if __name__ == "__main__":
    _git = GitParser()
    #_git.check_repo_isvalid('http://git.nextop.cc/systempublic/nextop-user.git')
    _git.get_branch_current_uuid('http://git.nextop.cc/systempublic/nextop-user.git',branch='release-user-20201110-v1.0.0')
    #_git.get_branch_current_uuid('http://git.nextop.cc/systempublic/nextop-user.git',branch='master')

