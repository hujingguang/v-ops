# Generated by Django 3.1 on 2020-11-27 04:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usermanage', '0013_auto_20201126_1048'),
    ]

    operations = [
        migrations.AddField(
            model_name='users',
            name='tel_num',
            field=models.CharField(blank=True, max_length=100, verbose_name='手机号码'),
        ),
    ]