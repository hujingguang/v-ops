# Generated by Django 3.1 on 2020-11-21 08:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deploymanage', '0003_appinfo_app_function'),
    ]

    operations = [
        migrations.AddField(
            model_name='appinfo',
            name='deploy_branch',
            field=models.CharField(default='master', max_length=200, verbose_name='服务提测分支'),
        ),
    ]
