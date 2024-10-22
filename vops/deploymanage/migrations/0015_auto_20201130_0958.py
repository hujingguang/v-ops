# Generated by Django 3.1 on 2020-11-30 01:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deploymanage', '0014_auto_20201130_0931'),
    ]

    operations = [
        migrations.AddField(
            model_name='deployapppublishrecord',
            name='deploy_status',
            field=models.CharField(choices=[('Pending', '待编译'), ('Compiling', '编译中'), ('CompileFailed', '编译失败'), ('DeployFailed', '部署失败'), ('DeployPass', '部署成功')], default='Pending', max_length=32, verbose_name='部署状态'),
        ),
        migrations.AddField(
            model_name='deployapppublishrecord',
            name='publish_status',
            field=models.IntegerField(choices=[(0, '未上线'), (1, '已上线'), (2, '上线中')], default=0, verbose_name='上线状态'),
        ),
    ]
