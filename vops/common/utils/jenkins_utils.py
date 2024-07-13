import jenkins
# from deploymanage.models import DeployAppEnv
# from common.conf import SysConfig
import logging
import time
from deploymanage.models import DeployAppRecord,DeployAppPublishRecord
from django.db import transaction

logger = logging.getLogger('default')


class JenkinsParser(object):

    def __init__(self, user, passwd, url):
        self._jenkins = None
        self._user = user
        self._passwd = passwd
        self._url = url
        self._job_full_name = None
        self._queue_id = None
        self.init_jenkins()

    def init_jenkins(self):
        if not self._jenkins:
            try:
                self._jenkins = jenkins.Jenkins(
                    self._url, self._user, self._passwd, timeout=30)
            except Exception as e:
                logger.error(str(e))
                self._jenkins = None
        return self._jenkins

    def start_job(self, deploy_id, job_full_name, parameters={'BRANCH':'master'}, depth=0, publish=False):
        """start_job. 触发一个job

        Args:
            job_full_name: job的全名
            parameters:  构建参数，默认为：{'BRANCH':'master'}
        """
        deploy_status = 'DeployFailed'
        queue_id = None
        result = [False, '-']
        if not self._jenkins:
            self.init_jenkins()
        try:
            if publish:
                with transaction.atomic():
                    DeployAppPublishRecord(publish_id=deploy_id,
                            deploy_status='Compiling',jenkins_log_url='').save(
                        update_fields=['deploy_status','jenkins_log_url'])
            else:
                with transaction.atomic():
                    DeployAppRecord(deploy_id=deploy_id,
                            deploy_status='Compiling',jenkins_log_url='').save(
                        update_fields=['deploy_status','jenkins_log_url'])

        except Exception as e:
            logger.error(str(e))

        try:
            queue_id = self._jenkins.build_job(
                job_full_name, parameters=parameters)
            if queue_id:
                result = self.check_job_result(
                    queue_id, job_full_name,
                    depth=depth,
                    deploy_id=deploy_id,
                    publish=publish)
                if result[0]:
                    deploy_status = 'DeployPass'
        except Exception as e:
            logger.error(str(e))

        try:
            if publish:
                with transaction.atomic():
                    DeployAppPublishRecord(publish_id=deploy_id, deploy_status=deploy_status,
                                    jenkins_log_url=result[1]).save(update_fields=['deploy_status', 'jenkins_log_url'])
            else:
                with transaction.atomic():
                    DeployAppRecord(deploy_id=deploy_id, deploy_status=deploy_status,
                                    jenkins_log_url=result[1]).save(update_fields=['deploy_status', 'jenkins_log_url'])
        except Exception as e:
            logger.error(str(e))
            print(str(e))



    def get_job_info(self, jobName, folderName=None, depth=0):
        """get_job_info. 获取jenkins工程信息

        Args:
            jobName: 工程名字
            folderName: 工程所属目录名
            depth:  目录深度

        Retruns:
            job_info: ['jobName','jobUrl','jobFullName']
        """
        if not self._jenkins:
            return None
        jobs = self._jenkins.get_all_jobs(folder_depth=depth)
        job_info = None
        if depth == 0:
            for job in jobs:
                if jobName == job['name']:
                    job_info = [job['name', job['url'], job['fullname']]]
        elif depth == 1 and folderName:
            for job in jobs:
                if folderName == job['name']:
                    for sub_job in job['jobs']:
                        if jobName == sub_job['name']:
                            job_info = [sub_job['name'],
                                        sub_job['url'], sub_job['fullname']]
        return job_info

    def check_job_result(self, queue_id, full_name, depth=0,deploy_id=None,publish=False):
        """check_job_result. 检测工程执行状态

        Args:
            queue_id: 工程触发后返回的队列id
            full_name: 工程全名(包含目录)
            depth: 工程目录深度

        Returns:
            True,job_log_url
            False,-
        """
        check_num = 5
        get_url = False
        n = 0
        while True:
            try:
                result = self._jenkins.get_job_info(full_name, depth)
                for build in result['builds']:
                    if build['queueId'] == queue_id:
                        if not get_url:
                            get_url = True
                            if deploy_id:
                                try:
                                    if publish:
                                        with transaction.atomic():
                                            DeployAppPublishRecord(publish_id=deploy_id,
                                                    jenkins_log_url=build['url']+'console').save(update_fields=['jenkins_log_url'])
                                    else:
                                        with transaction.atomic():
                                            DeployAppRecord(deploy_id=deploy_id,
                                                    jenkins_log_url=build['url']+'console').save(update_fields=['jenkins_log_url'])
                                except Exception as e:
                                    pass
                        if not build['building']:
                            check_num = check_num - 1
                            # 确认检测五次后退出
                            if check_num != 0:
                                continue
                            if build['result'] == "SUCCESS":
                                return True, build['url'] + 'console'
                            else:
                                return False, build['url'] + 'console'
                time.sleep(3)
            except Exception as e:
                logger.error(str(e))
                break
        return False, '-'



