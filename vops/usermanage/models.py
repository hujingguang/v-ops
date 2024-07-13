from django.db import models
from django.contrib.auth.models import AbstractUser
from mirage import fields

# Create your models here.


class Config(models.Model):
    """Config. 保存系统配置类
    """
    item = models.CharField('配置项', max_length=200, primary_key=True)
    value = fields.EncryptedCharField(verbose_name='配置值', max_length=500)
    description = models.CharField(
        '配置项值', max_length=500, default='', blank=True)

    class Meta:
        managed = True
        db_table = 'vops_config'
        verbose_name = u'系统配置'
        verbose_name_plural = u'系统配置'


class Users(AbstractUser):
    """Users. 用户类
    """

    display = models.CharField('姓名', max_length=50, default='')
    tel_num = models.CharField('手机号码', max_length=100, blank=True)
    ding_user_id = models.CharField('钉钉用户ID', max_length=100, blank=True)
    wx_user_id = models.CharField('企业微信用户ID', max_length=100, blank=True)
    feishu_open_id = models.CharField('飞书用户ID', max_length=100, blank=True)
    failed_login_count = models.IntegerField('登录失败次数', default=0)
    last_login_failed_at = models.DateTimeField(
        '上次登录失败', blank=True, null=True)

    def save(self, *args, **kwargs):
        self.failed_login_count = min(127, self.failed_login_count)
        self.failed_login_count = max(0, self.failed_login_count)
        super(Users, self).save(*args, **kwargs)

    def __str__(self):
        """__str__.
        在base.html基础模版中显示登陆用户名
        """
        if self.display:
            return self.display
        return self.username

    class Meta:
        managed = True
        db_table = 'vops_users'
        verbose_name = u'用户信息表'
        verbose_name_plural = u'用户信息表'


class Permission(models.Model):
    """Permission. 权限类对象
    """
    class Meta:
        permissions = (
            ('menu_dashboard', '菜单 Dashboard'),
            ('menu_system_configure', '菜单 系统配置'),
            ('menu_deploymanage', '菜单 发布管理'),
            ('menu_deploymanage_servicemanage', '菜单 服务定义 服务列表'),
            ('menu_deploymanage_bindservice', '菜单 服务定义 服务绑定'),
            ('menu_deploymanage_addservice', '菜单 服务定义 服务添加'),
            ('menu_deploymanage_delservice', '菜单 服务定义 服务删除'),
            ('menu_deploymanage_resetservice', '菜单 服务定义 依赖重置'),
            ('menu_deploymanage_getservice', '菜单 服务定义 服务获取'),
            ('menu_deploymanage_updateservice', '菜单 服务定义 服务修改'),

            ('menu_deploymanage_versiontest', '菜单 版本提测 版本列表'),
            ('menu_deploymanage_addversion', '菜单 版本提测 添加版本'),
            ('menu_deploymanage_getversion', '菜单 版本提测 获取版本'),
            ('menu_deploymanage_updateversion', '菜单 版本提测 修改版本'),
            ('menu_deploymanage_passversion', '菜单 版本提测 版本测试操作'),
            ('menu_deploymanage_deployversion', '菜单 版本提测 发布版本'),


            ('menu_deploymanage_versionpublish', '菜单 版本上线 版本列表'),
            ('menu_deploymanage_addpublish', '菜单 版本上线 添加上线版本'),
            ('menu_deploymanage_getpublish', '菜单 版本上线 获取上线版本'),
            ('menu_deploymanage_updatepublish', '菜单 版本上线 更新上线版本'),
        )
