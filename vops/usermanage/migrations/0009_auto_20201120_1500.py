# Generated by Django 3.1 on 2020-11-20 07:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('usermanage', '0008_auto_20201120_1157'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='permission',
            options={'permissions': (('menu_dashboard', '菜单 Dashboard'), ('menu_system_configure', '菜单 系统配置'), ('menu_deploymanage', '菜单 发布管理'), ('menu_deploymanage_servicemanage', '菜单 微服务管理'), ('menu_deploymanage_bindservice', '菜单 微服务管理 服务绑定'), ('menu_deploymanage_addservice', '菜单 微服务管理 服务添加'), ('menu_deploymanage_delservice', '菜单 微服务管理 服务删除'), ('menu_deploymanage_resetservice', '菜单 微服务管理 服务依赖重置'), ('menu_deploymanage_getservice', '菜单 微服务管理 服务获取'), ('menu_deploymanage_updateservice', '菜单 微服务管理 服务修改'))},
        ),
    ]
