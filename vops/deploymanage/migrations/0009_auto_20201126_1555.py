# Generated by Django 3.1 on 2020-11-26 07:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deploymanage', '0008_auto_20201126_0917'),
    ]

    operations = [
        migrations.AddField(
            model_name='deployappenv',
            name='jenkins_folder',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='jenkins工程的目录'),
        ),
        migrations.AddField(
            model_name='deployappenv',
            name='jenkins_url',
            field=models.CharField(blank=True, max_length=500, null=True, verbose_name='jenkins地址'),
        ),
    ]
