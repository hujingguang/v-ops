# Generated by Django 3.1 on 2020-11-24 07:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deploymanage', '0005_appversionrecord_deployappenv_deployapppublishrecord_deployapppublishrecorddetail_deployapprecord_de'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deployappenv',
            name='env_kubeconf',
            field=models.TextField(default='', null=True, verbose_name='环境k8s配置文件'),
        ),
        migrations.AlterField(
            model_name='deployappenv',
            name='env_namespace',
            field=models.CharField(blank=True, default='', max_length=24, null=True, verbose_name='环境k8s命名空间'),
        ),
    ]
