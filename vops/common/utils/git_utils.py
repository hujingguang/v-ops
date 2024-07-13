import git
import logging
import tempfile
import os
from urllib.parse import quote
from common.config import SysConfig
from common.utils import xml_utils
import subprocess
import time


logger = logging.getLogger('default')


class GitParser(object):

    def __init__(self):
        _conf = SysConfig()
        self.git_user = _conf.get('git_username')
        self.git_password = _conf.get('git_password')
        self.git_server = _conf.get('git_server_address')
        self.git_repo_address = None

    def init_repo_env(self, repoName=None):
        if not self.git_user or not self.git_server or not self.git_password or not repoName:
            logger.error('Git配置缺失,无法进行git操作初始化')
            print(self.git_user, self.git_password, repoName, self.git_server)
        else:
            repoName = repoName.split('://')
            if len(repoName) != 2:
                logger.error('输入的代码库地址格式有问题,')
            else:
                user_pass = ':'.join(
                    [quote(self.git_user), quote(self.git_password)])
                self.git_repo_address = repoName[0] + \
                    '://' + user_pass + "@" + repoName[1]


    def delete_remote_branch(self,repoName,branch):
        if not self.git_repo_address:
            self.init_repo_env(repoName)
        _repo_with_auth = self.git_repo_address
        if not _repo_with_auth:
            return {'status': 1, 'msg': '代码库验证失败', 'data': []}
        with tempfile.TemporaryDirectory() as _dir:
            try:
                git.Repo.clone_from(_repo_with_auth, _dir, branch=branch)
                repo =  git.Repo(_dir)
                push_branch = ':'+branch
                repo.remote().push(refspec=push_branch)
            except Exception as e:
                logger.error(str(e))
                return {'status': 1, 'msg': '远程分支：{0} 删除失败'.format(branch), 'data': []}
            return {'status': 0, 'msg': 'ok', 'data': []}



    def check_repo_is_valid(self, repoName, pom_file=None, branch='master',
            is_java=True):
        """check_repo_is_valid. 检测一个git仓库是否有效

        Args:
            repoName: git仓库地址
            pom_file: 工程pom文件路径
            branch: 工程分支
            is_java: 是否为java工程,默认为True
        """
        if not self.git_repo_address:
            self.init_repo_env(repoName)
        _repo_with_auth = self.git_repo_address
        if not _repo_with_auth:
            return {'status': 1, 'msg': '代码库验证失败', 'data': []}
        with tempfile.TemporaryDirectory() as _dir:
            try:
                git.Repo.clone_from(_repo_with_auth, _dir, branch=branch)
            except Exception as e:
                logger.error(str(e))
                _e = str(e).split('\n')[-3] + str(e).split('\n')[-2]
                _e = '检测失败,错误如下：\n'+_e
                return {'status': 1, 'msg': _e, 'data': []}
            if pom_file and is_java:
                _pom_file = os.path.join(
                    os.path.join(_dir, pom_file), 'pom.xml')
                if not os.path.exists(_pom_file):
                    return {'status': 1, 'msg': 'pom.xml 不存在', 'data': []}
        return {'status': 0, 'msg': '检测通过,添加成功', 'data': []}


    def get_service_branch_list(self, repoName, branch='master',
            prefix='feature',last_num=10,app_type=1):
        """get_service_branch_list. 动态获取工程分支

        Args:
            repoName: git代码库地址
            branch: 默认分支
            prefix: 分支筛选前缀
            last_num: 最近几个分支
            app_type: 工程类型，前端为0 java为1 默认为1.
        """
        if not self.git_repo_address:
            self.init_repo_env(repoName)
        if not self.git_repo_address:
            return {'status': 1, 'msg': '代码库验证失败,请检查git仓库配置', 'data': []}
        with tempfile.TemporaryDirectory() as _dir:
            try:
                branches_list = list()
                git.Repo.clone_from(self.git_repo_address, _dir)
                repo = git.Repo(_dir)
                branches = repo.remote().refs
                for branch in branches:
                    if branch.name.startswith('origin/' + prefix):
                        if app_type == 0:
                            branch = branch.name.replace('origin/','')
                        else:
                            branch = branch.name.replace('origin/','').split('/')[-1]
                        branches_list.append(branch)
                return {'status':0,'msg':'ok','data': branches_list}
            except Exception as e:
                _e = str(e).split('\n')[-2]
                _e = '检测失败,错误如下：\n'+_e
                return {'status': 1, 'msg': _e, 'data': []}


    def get_branch_commit_uuid(self, repoName, branch,
            auto_create_test_branch=False, prefix='feature'):
        """get_branch_commit_uuid. 获取一个分支当前的代码的uuid

        Args:
            repoName: git仓库地址
            branch: 分支名
            auto_create_test_branch: 是否自动从该分支创建一个测试分支，默认为False
            prefix: 自动测试分支替换前缀
        """
        result = None
        repo = None
        uuid = None
        if not self.git_repo_address:
            self.init_repo_env(repoName)
        if not self.git_repo_address:
            return {'status': 1, 'msg': '代码库验证失败,请检查git仓库配置', 'data': []}
        with tempfile.TemporaryDirectory() as _dir:
            try:
                git.Repo.clone_from(self.git_repo_address, _dir, branch=branch)
                repo = git.Repo(_dir)
                uuid = repo.commit(branch).__str__()
                result = [uuid]
            except Exception as e:
                logger.error(str(e))
                _e = str(e).split('\n')[-2]
                _e = '检测失败,错误如下：\n'+_e
                return {'status': 1, 'msg': _e, 'data': []}
            if auto_create_test_branch:
                result = self.auto_create_test_branch(repo, branch,
                        uuid,prefix=prefix)
        return result

    def deploy_jar_to_repo(self, project, 
            repoName, 
            branch, 
            jar_version, 
            pom_path, 
            maven_path,
            action=0,
            push=False,
            parent='nextop-base-parent',
            parent_jar_version='',
            relation_project=dict(),
            is_deploy=True
            ):
        """deploy_jar_to_repo. 编译工程并deploy包到maven仓库以及提交修改到git

        Args:
            project: 需要编译的工程名
            repoName: 工程的git代码地址
            branch:   工程的分支名
            jar_version: 发布到仓库饿jar包名字
            pom_path:  工程的pom文件相对路径
            maven_path: maven二进制工具的绝对目录路径
            action:  修改pom文件动作：0|1|2  0表示设置自己服务的版本号 1表示设置parent包版本， 2表示设置依赖包的版本
            push: 是否将pom文件修改push到Git仓库,默认不推送
            parent: 如果action=1,则表示parent包的工程名
            parent_jar_version: 如果action=1,则表示parent包的版本名
            relation_project: 如果action=2,则表示依赖包名及其发布包版本名对应字典
            is_deploy: 是否进行mvn编译并推送到nexus仓库操作,默认推送
        """
        maven_bin = os.path.join(maven_path, 'mvn')
        if not self.git_repo_address:
            self.init_repo_env(repoName)
        if not self.git_repo_address:
            return {'status': 1, 'msg': '代码库验证失败,请检查git仓库配置', 'data': []}
        if not os.path.exists(maven_bin):
            return {'status': 1, 'msg': 'maven工具不存在,请检查配置', 'data': []}
        with tempfile.TemporaryDirectory() as _dir:
            try:
                git.Repo.clone_from(self.git_repo_address, _dir, branch=branch)
                repo =  git.Repo(_dir)
                work_dir = os.path.join(_dir, pom_path)
                pom_file = os.path.join(work_dir, 'pom.xml')
                #为0表示设置服务自己的版本deploy和push
                if action == 0:
                    exec_result = xml_utils.set_project_and_version(
                        pom_file, project, jar_version)
                    if not exec_result:
                        return {'status': 1, 'msg': '工程：{0} pom文件解析失败'.format(project), 'data': []}
                    shell = 'cd {0} && {1} deploy'.format(work_dir, maven_bin)
                    code = 1
                    if is_deploy:
                        code, stdout = subprocess.getstatusoutput(shell)
                    else:
                        code = 0
                        #不是parent包不发布
                    if code != 0:
                        return {'status': 1, 'msg': '工程：{0} 发布包到nexus失败'.format(project), 'data': []}
                    else:
                        if push:
                            #是否将修改推送到分支
                            repo.index.add(pom_file)
                            repo.index.commit('运维自动更新服务版本')
                            #origin_branch = branch + ':' + branch
                            repo.remotes.origin.push()
                        return {'status': 0, 'msg': 'ok', 'data': [branch, jar_version]}
                elif action == 1:
                    # 1表示依赖包替换parent包及其版本和push
                    exec_result = xml_utils.set_parent_version(pom_file,parent,parent_jar_version)
                    if not exec_result:
                        return {'status': 1, 'msg': '工程：{0} pom文件解析失败'.format(project), 'data': []}
                    shell = 'cd {0} && {1} deploy'.format(work_dir, maven_bin)
                    if is_deploy:
                        code, stdout = subprocess.getstatusoutput(shell)
                    else:
                        code = 0
                    if code != 0:
                        return {'status': 1, 'msg': '工程：{0} 发布包到nexus失败'.format(project), 'data': []}
                    if push:
                        #是否将修改推送到分支
                        repo.index.add(pom_file)
                        repo.index.commit('运维自动更新服务parent包版本')
                        repo.remotes.origin.push()
                    return {'status': 0, 'msg': 'ok', 'data': []}
                elif action == 2:
                    # 2 表示替换依赖包及其版本并deploy和push
                    for p, v in  relation_project.items():
                        exec_result = xml_utils.set_dependence_and_version(pom_file,p,v)
                        if not exec_result:
                            return {'status': 1, 'msg': '工程：{0} 依赖包： {1} pom文件版本替换失败失败'.format(project,p), 'data': []}
                    shell = 'cd {0} && {1} deploy'.format(work_dir, maven_bin)
                    if is_deploy:
                        code, stdout = subprocess.getstatusoutput(shell)
                    else:
                        code = 0
                    if code != 0:
                        return {'status': 1, 'msg': '工程：{0} 发布包到nexus失败'.format(project), 'data': []}
                    if push:
                        #是否将修改推送到分支
                        repo.index.add(pom_file)
                        repo.index.commit('运维自动更新服务依赖包版本')
                        #origin_branch = branch + ':' + branch
                        #repo.remotes.origin.push(refspec=origin_branch)
                        repo.remotes.origin.push()
                    return {'status': 0, 'msg': 'ok', 'data': [branch, jar_version]}
            except Exception as e:
                _e = str(e)
                return {'status': 1, 'msg': _e, 'data': []}


    def merge_branch_to_other(self, repoName, s_branch, t_branch):
        """merge_branch_to_other. 自动合并分支

        Args:
            repoName: 库地址
            s_branch: 需要合并分支
            t_branch: 获取代码分支
        """
        if not self.git_repo_address:
            self.init_repo_env(repoName)
        if not self.git_repo_address:
            return {'status': 1, 'msg': '代码库验证失败,请检查git仓库配置', 'data': []}
        with tempfile.TemporaryDirectory() as _dir:
            try:
                git.Repo.clone_from(self.git_repo_address, _dir, branch=s_branch)
                repo = git.Repo(_dir)
                _git = repo.git
                _git.checkout('origin/' + t_branch)
                tb = repo.head
                _git.checkout(s_branch)
                #repo.index.merge_tree(tb)
                cmd = 'cd ' + _dir + '&& git merge origin/'+t_branch
                _r = os.system(cmd)
                if _r != 0:
                    raise  Exception('代码同步失败')
                repo.index.commit('Auto Sync to test branch by it.ops')
                #_git.checkout('origin/'+t_branch)
                branch_map = s_branch + ':' + s_branch
                repo.remotes.origin.push(refspec=branch_map)
                return {'status': 0, 'msg': 'ok', 'data': []}
            except Exception as e:
                print(str(e))
                return {'status': 1, 'msg': '自动同步代码失败,请手动推送到提测分支', 'data': []}

    def merge_branch_and_create_release(self, repoName, branches, release_name, app_name='', pom_data=None,branches_uuid=dict()):
        """merge_branch_and_create_release. 合并分支并创建release分支名

        Args:
            repoName:  工程仓库地址
            branches: 分支列表 type: list
            release_name: 发布分支名字
            app_name: 工程服务名
            pom_data: pom文件数据,废弃无用
            branches_uuid: 如果有多个分支合并,分支对应uuid字典
        """
        if not self.git_repo_address:
            self.init_repo_env(repoName)
        if not self.git_repo_address:
            return {'status': 1, 'msg': '代码库验证失败,请检查git仓库配置', 'data': []}
        with tempfile.TemporaryDirectory() as _dir:
            b = branches[0]
            repo = None
            _git = None
            try:
                print('开始合并分支')
                git.Repo.clone_from(self.git_repo_address, _dir, branch=b)
                repo = git.Repo(_dir)
                _git = repo.git
                repo.create_head(release_name)
                _git.checkout(release_name)
                if b in branches_uuid and len(branches_uuid[b])>10:
                    repo.index.reset(commit=branches_uuid[b], head=True)
                print('初始化并推送发布分支')
                branch_map = release_name + ':' + release_name
                repo.remotes.origin.push(refspec=branch_map)
            except Exception as e:
                print(str(e))
                return {'status': 1, 'msg': '服务{0} 分支：{1} 检出代码失败: {2}'.format(app_name, b, str(e)), 'data': []}
            if len(branches) > 1:
                try:
                    for _b in branches:
                        if _b != b:
                            cmd = 'cd '+_dir+' && git fetch origin ' + _b
                            _r = os.system(cmd)
                            if _r != 0:
                                raise Exception()
                            #_git.checkout('origin/'+_b)
                            _git.checkout(_b)
                            if _b in branches_uuid and len(branches_uuid[_b]) > 10:
                                #如果有明确的分支uuid, 则严格按照uuid位置合并代码
                                repo.index.reset(commit=branches_uuid[_b], head=True)
                            #merge_branch = repo.head
                            cmd = 'cd ' + _dir + ' && git merge ' + _b
                            _git.checkout(release_name)
                            _r = os.system(cmd)
                            if _r != 0:
                                raise Exception()
                            #repo.index.merge_tree(merge_branch)
                            repo.index.commit('Auto merge by it.ops')
                except Exception as e:
                    return {'status': 1, 'msg': '服务{0} 合并分支：{1} 失败'.format(app_name, _b), 'data': []}
            try:
                if pom_data:
                    pass
                print('开始重新推送合并后的发布分支')
                branch_map = release_name + ':' + release_name
                repo.remotes.origin.push(refspec=branch_map)
                return {'status': 0, 'msg': 'ok', 'data': []}
            except Exception as e:
                return {'status': 1, 'msg': '服务{0} 推送分支：{1} 失败'.format(app_name, release_name), 'data': []}


    def update_pom_and_push_release(self,release_name):
        pass

    def auto_create_test_branch(self, repo, branch, uuid, prefix='feature'):
        """auto_create_test_branch. 自动生成测试分支

        Args:
            repo: git仓库对象
            branch: 提测分支
            uuid: 提测分支代码位置
            prefix: 默认替换前缀
        """
        test_branch_name = None
        if branch.startswith(prefix):
            test_branch_name = branch.replace(prefix, 'auto.test')
        elif branch.startswith('release'):
            test_branch_name = branch.replace('release', 'auto.test')
        else:
            return {'status': 1, 'msg': '提测分支格式错误,命名必须以feature开头不存在', 'data': []}
        try:
            test_branch = repo.create_head(test_branch_name, uuid)
            test_branch.checkout()
            test_branch.repo.git.push('--set-upstream', 'origin', test_branch)
            return [test_branch_name, uuid]
        except Exception as e:
            logger.error(str(e))
            return {'status': 1, 'msg': str(e), 'data': []}


if __name__ == "__main__":
    _git = GitParser()
