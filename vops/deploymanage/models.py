from django.db import models


APP_TYPE = (
    (0, 'Node-微服务'),
    (1, 'Java-微服务'),
    (2, 'Java-API服务'),
)


class AppInfo(models.Model):
    """AppInfo. 服务定义信息
    """
    app_name = models.CharField('服务名', max_length=100, primary_key=True)
    git_repo_address = models.CharField('服务Git地址', max_length=200, blank=False)
    deploy_branch = models.CharField('服务提测分支', max_length=200,
                                     default="master", blank=False)
    pom_xml_path = models.CharField(
        'pom文件路径', max_length=200, blank=True)
    create_time = models.DateTimeField('创建时间')
    update_time = models.DateTimeField('更新时间', blank=True, null=True)
    app_type = models.IntegerField('服务类型', choices=APP_TYPE)
    create_user = models.CharField('创建人', max_length=32, null=False)
    app_function = models.CharField('所属业务', max_length=32, default="其他")
    #base_parent = models.CharField('全局基础服务名',max_length=100,default='nextop-base-parent')

    class Meta:
        managed = True
        db_table = 'vops_deploy_app_info'
        verbose_name = '微服务信息'
        verbose_name_plural = '微服务信息'


class AppRelationShip(models.Model):
    """AppRelationShip. 服务依赖关系表
    """

    r_id = models.AutoField('关系ID', primary_key=True)
    app_name = models.CharField('服务名', max_length=100)
    with_apps = models.CharField('依赖服务', max_length=500, blank=True, null=True)
    create_user = models.CharField('创建人', max_length=32, null=False)
    create_time = models.DateTimeField('创建时间')
    update_time = models.DateTimeField('更新时间', blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'vops_deploy_app_relationship'
        verbose_name = '微服务依赖关系'
        verbose_name_plural = '微服务依赖关系'


class DeployAppEnv(models.Model):
    """DeployEnv. 服务部署环境
    """
    env_id = models.AutoField('环境id', primary_key=True)
    env_name = models.CharField('环境名', max_length=32, blank=True)
    env_description = models.TextField('环境描述', default='')
    env_kubeconf = models.TextField('环境k8s配置文件', default='', null=True)
    env_namespace = models.CharField(
        '环境k8s命名空间', max_length=24, blank=True, default='', null=True)
    jenkins_url = models.CharField(
        'jenkins地址', max_length=500, null=True, blank=True)
    jenkins_folder = models.CharField(
        'jenkins工程的目录', max_length=100, blank=True, null=True)
    project_prefix = models.CharField(
        'jenkins工程前缀', max_length=30, null=True, blank=True)
    project_sufix = models.CharField(
        'jenkins工程后缀', max_length=30, null=True, blank=True)
    jenkins_folder_depth = models.IntegerField(
        'jenkins工程目录深度', default=0, blank=True)
    can_select = models.IntegerField('环境是否可选', null=True, default=1)

    def __str__(self):
        return self.env_name

    class Meta:
        managed = True
        db_table = 'vops_deploy_app_env'
        verbose_name = '部署环境'
        verbose_name_plural = '部署环境'


DEPLOY_STATUS_CHOICE = (
    ('Pending', '待编译'),
    ('Compiling', '编译中'),
    ('CompileFailed', '编译失败'),
    ('DeployFailed', '部署失败'),
    ('DeployPass', '部署成功'),
)

TEST_STATUS_CHOICE = (
    ('WaitTest', '待测试'),
    ('TestNotPass', '未通过测试'),
    ('TestPass', '测试通过'),
)

IS_PUBLISH_CHOICE = (
    (0, '未上线'),
    (1, '已上线'),
    (2, '上线中'),
)


class DeployAppRecord(models.Model):
    """AppDeploy. 服务部署记录表
    """
    deploy_id = models.AutoField('服务发布记录id', primary_key=True)
    app_name = models.CharField('服务名', max_length=100)
    feature_branch = models.CharField('提测特性分支名', max_length=128)
    feature_branch_uuid = models.CharField('提测特性分支UUID', max_length=500)

    auto_test_branch = models.CharField('提测生成测试分支', max_length=128)
    auto_test_branch_uuid = models.CharField('提测生成测试分支UUID', max_length=500)

    deploy_status = models.CharField('发布状态', max_length=32,
                                     choices=DEPLOY_STATUS_CHOICE)
    test_status = models.CharField(
        '测试状态', max_length=32, choices=TEST_STATUS_CHOICE)
    publish_status = models.IntegerField(
        '上线状态', choices=IS_PUBLISH_CHOICE, default=0)
    publish_time = models.DateTimeField('上线时间', blank=True, null=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', auto_now=True)

    create_user = models.CharField('创建人', max_length=32)
    test_user = models.CharField('测试人', max_length=32)
    description = models.TextField('功能描述', default=' ', null=True, blank=True)
    jenkins_log_url = models.CharField(
        'jenkins日志url', max_length=500, null=True, blank=True)
    deploy_env = models.ManyToManyField(
        DeployAppEnv, verbose_name="发布环境", blank=True)
    is_sync = models.IntegerField(
        '是否开始代码同步', choices=((0, '不同步'), (1, '同步')), default=0)
    is_deleted = models.IntegerField(
        '分支是否已删除', choices=((0, '未删除'), (1, '已删除')), default=0)

    class Meta:
        managed = True
        db_table = 'vops_deploy_app_record'
        verbose_name = '服务提测记录表'
        verbose_name_plural = '服务提测记录表'


class DeployAppRecordDetail(models.Model):
    """AppDeployDetail. 服务部署详情表
    """
    detail_id = models.AutoField('服务发布详情id', primary_key=True)
    compile_log = models.TextField('编译日志', default='')
    deploy_log = models.TextField('部署日志', default='')
    update_log = models.TextField('操作日志', default='')
    test_image_url = models.CharField('提测镜像地址',
                                      max_length=500, blank=True, null=True)
    deploy_app_record = models.OneToOneField(
        DeployAppRecord, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'vops_deploy_app_record_detail'
        verbose_name = '服务提测记录详情表'
        verbose_name_plural = '服务提测记录详情表'


class DeployAppPublishRecord(models.Model):
    """DeployAppPublishRecord. 服务上线记录表
    """

    publish_id = models.AutoField('服务上线记录id', primary_key=True)
    app_name = models.CharField('服务名', max_length=200, null=True)
    description = models.TextField('上线描述', default='')
    deploy_ids = models.CharField('提测记录ID列表', max_length=32)
    dependence_str = models.TextField('依赖包及分支列表 以,分隔', null=True)
    create_user = models.CharField('创建人', max_length=32)
    publish_user = models.CharField('验证人', max_length=32, null=True)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    update_time = models.DateTimeField('更新时间', blank=True, null=True)
    publish_env = models.ManyToManyField(
        DeployAppEnv, verbose_name='上线环境', blank=True)
    publish_status = models.IntegerField(
        '上线状态', choices=IS_PUBLISH_CHOICE, default=0)
    deploy_status = models.CharField(
        '部署状态', max_length=32, choices=DEPLOY_STATUS_CHOICE, default='Pending')
    jenkins_log_url = models.CharField(
        'jenkins日志链接', max_length=500, null=True)
    release_status = models.IntegerField('版本生成状态', choices=(
        (0, '待生成'), (1, '已生成'), (2, '生成失败')), default=0)
    branch_status = models.IntegerField('分支状态',choices=((0,'未合并'),(1,'已合并')),default=0)
    merge_status = models.IntegerField('合并状态',choices=((0,'无冲突'),(1,'有冲突')),default=0)

    class Meta:
        managed = True
        db_table = 'vops_publish_record'
        verbose_name = '服务上线记录表'
        verbose_name_plural = '服务上线记录表'


class DeployAppPublishRecordDetail(models.Model):
    """DeployAppPublishRecordDetail. 服务上线记录详情表
    """

    detail_id = models.AutoField('服务上线详情id', primary_key=True)
    compile_log = models.TextField('编译日志', default='')
    deploy_log = models.TextField('部署日志', default='')
    update_log = models.TextField('操作日志', default='')
    release_image_url = models.CharField(
        '上线镜像地址', max_length=500, blank=True, null=True)
    deploy_app_publish_record = models.OneToOneField(
        DeployAppPublishRecord, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'vops_publish_record_detail'
        verbose_name = '服务上线详情表'
        verbose_name_plural = '服务上线详情表'


class AppVersionRecord(models.Model):
    """AppDeployVersion. 服务部署生成版本信息表
    """
    version_id = models.AutoField('服务版本id', primary_key=True)
    publish_id = models.IntegerField('服务上线id')
    app_name = models.CharField('服务名', max_length=64)
    feature_branch = models.CharField('提测分支名', max_length=128)
    test_branch = models.CharField('测试分支名', max_length=128)
    test_branch_uuid = models.CharField('当前提测分支commit uuid', max_length=128)
    release_branch = models.CharField('生成release分支名', max_length=64)
    release_branch_uuid = models.CharField('生成release分支uuid', max_length=64)
    publish_tag = models.CharField('生成tag名字', max_length=64)
    maven_jar_version = models.CharField('依赖包maven仓库版本号', max_length=64)
    parent_app_name = models.CharField(
        '父工程服务名', max_length=128, null=True, blank=True)
    child_app_name = models.CharField(
        '子工程服务名', max_length=128, null=True, blank=True)
    create_time = models.DateTimeField('创建时间', null=True)
    service_relation = models.CharField(
        '服务对应关系', max_length=500, null=True, blank=True)
    is_conflicted = models.IntegerField('合并是否有冲突',choices=((0,'否'),(1,'是')),default=0)

    class Meta:
        managed = True
        db_table = 'vops_deploy_app_version'
        verbose_name = '服务部署版本记录表'
        verbose_name_plural = '服务部署版本记录表'


class AppVersionHistory(models.Model):
    history_id = models.AutoField('版本历史表id', primary_key=True)
    publish_id = models.IntegerField('服务上线id', null=True)
    app_name = models.CharField('服务名', max_length=500)
    release_name = models.CharField(
        '版本名', max_length=500, null=True, blank=True)
    release_uuid = models.CharField('生成release分支uuid',
                                    max_length=64, null=True)
    create_time = models.DateTimeField('创建时间')
    maven_jar_version = models.CharField('依赖包maven仓库版本号',
                                         max_length=64, null=True)
    service_relation = models.CharField(
        '服务对应关系', max_length=500, null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'vops_deploy_app_version_history'
        verbose_name = '服务版本历史记录表'
        verbose_name_plural = '服务版本历史记录表'


class AppBranchStatus(models.Model):
    branch_id = models.AutoField('分支id', primary_key=True)
    app_name = models.CharField('服务名', max_length=100)
    branch_name = models.CharField('分支名字', max_length=500)
    is_deleted = models.IntegerField(
        '是否已删除', choices=((0, '未删除'), (1, '已删除')), default=0)
    is_merged = models.IntegerField(
        '合并状态', choices=((0, '未合并'), (1, '已合并')), default=0)
    branch_type = models.IntegerField('分支类型', choices=(
        (0, '功能分支'), (1, '测试分支'), (2, '发布分支')), default=0)
    create_time = models.DateTimeField('创建时间', auto_now_add=True)
    create_by = models.CharField('操作人', max_length=32)

    class Meta:
        managed = True
        db_table = 'vops_deploy_branch_status'
        verbose_name = '分支状态表'
        verbose_name_plural = '分支状态表'



class VmHostInfo(models.Model):
    uid = models.AutoField('虚拟机id',primary_key=True)
    hostname = models.CharField('虚拟机名', max_length=200)
    ip = models.CharField('虚拟机IP', max_length=32)
    physical_hostname =  models.CharField('宿主机名', max_length=200)
    is_deleted = models.IntegerField('是否删除',choices=((0,'未删除'),(1,'已删除')), default=0)
    group = models.CharField('主机所属业务组', max_length=200, null=True)
    area = models.CharField('主机所属区域', max_length=200, null=True)
    remark = models.CharField('备注', max_length=500, null=True)
    vm_id = models.CharField('虚拟机id', max_length=64, null=True)
    is_inited = models.IntegerField('是否初始化',choices=((0,'否'),(1,'是')), default=0)

    class Meta:
        managed = True
        db_table = 'vm_hosts'
        verbose_name = '虚拟机列表'
        verbose_name_plural = '虚拟机列表'







