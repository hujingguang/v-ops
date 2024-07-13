import git
import tempfile
import os
from urllib.parse import quote


class GitParser(object):

    def __init__(self):
        #self.git_user = "843533046@qq.com"
        self.git_user = "it.ops"
        self.git_password = 'SqFYVVeeo2Rd2*QIEM11'
        #self.git_password = 'hu5340864'
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

    def get_branch_current_uuid(self,repoName,branch=None):
        _r = self.init_repo_env(repoName)
        if _r:
            print(_r[1])
            os.system('mkdir -p ' + _r[1])
            try:
                git.Repo.clone_from(_r[0],_r[1],branch=branch)
                repo = git.Repo(_r[1])
                #print(repo.active_branch)
                #print(dir(repo.branches[0]))
                #print(dir(repo.branches[0].log().index(1)))
                commit = repo.commit(branch)
                uuid = commit.__str__()
                print(type(uuid))
                #print(repo.tags)
                #print(dir(repo))
            except Exception as e:
                print(str(e))


    def create_auto_test_branch(self,repoName,from_branch):
        pass


if __name__ == "__main__":
    _git = GitParser()
    #_git.check_repo_isvalid('http://git.nextop.cc/nextop-ops/v-ops.git')
    #_git.check_repo_isvalid('http://git.nextop.cc/systempublic/nextop-user.git')
    _git.get_branch_current_uuid('http://git.nextop.cc/systempublic/nextop-user.git',branch='release-user-20201110-v1.0.0')
    #_git.get_branch_current_uuid('http://git.nextop.cc/systempublic/nextop-user.git',branch='master')

