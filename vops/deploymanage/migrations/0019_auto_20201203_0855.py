# Generated by Django 3.1 on 2020-12-03 00:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deploymanage', '0018_deployapppublishrecord_publish_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='appversionhistory',
            name='maven_jar_version',
            field=models.CharField(max_length=64, null=True, verbose_name='依赖包maven仓库版本号'),
        ),
        migrations.AddField(
            model_name='appversionhistory',
            name='publish_id',
            field=models.IntegerField(null=True, verbose_name='服务上线id'),
        ),
    ]