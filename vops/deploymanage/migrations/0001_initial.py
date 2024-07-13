# Generated by Django 3.1 on 2020-11-18 02:33

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AppInfo',
            fields=[
                ('app_name', models.CharField(max_length=100, primary_key=True, serialize=False, verbose_name='服务名')),
                ('git_repo_address', models.CharField(max_length=200, verbose_name='服务Git地址')),
                ('pom_xml_path', models.CharField(blank=True, max_length=200, verbose_name='pom文件路径')),
                ('create_time', models.DateTimeField(verbose_name='创建时间')),
                ('update_time', models.DateTimeField(blank=True, null=True, verbose_name='更新时间')),
                ('app_type', models.IntegerField(choices=[('0', 'Node-微服务'), ('1', 'Java-微服务'), ('2', 'Java-API服务')], verbose_name='服务类型')),
                ('create_user', models.CharField(max_length=32, verbose_name='创建人')),
            ],
            options={
                'verbose_name': '微服务信息',
                'verbose_name_plural': '微服务信息',
                'db_table': 'vops_deploy_app_info',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='AppRelationShip',
            fields=[
                ('r_id', models.AutoField(primary_key=True, serialize=False, verbose_name='关系ID')),
                ('app_name', models.CharField(max_length=100, verbose_name='服务名')),
                ('with_apps', models.CharField(blank=True, max_length=500, null=True, verbose_name='依赖服务')),
                ('create_user', models.CharField(max_length=32, verbose_name='创建人')),
                ('create_time', models.DateTimeField(verbose_name='创建时间')),
                ('update_time', models.DateTimeField(blank=True, null=True, verbose_name='更新时间')),
            ],
            options={
                'verbose_name': '微服务依赖关系',
                'verbose_name_plural': '微服务依赖关系',
                'db_table': 'vops_deploy_app_relationship',
                'managed': True,
            },
        ),
    ]