# Generated by Django 3.1 on 2020-12-05 08:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deploymanage', '0022_deployappenv_can_select'),
    ]

    operations = [
        migrations.AddField(
            model_name='deployapprecord',
            name='is_sync',
            field=models.IntegerField(choices=[(0, '不同步'), (1, '同步')], default=0, verbose_name='是否开始代码同步'),
        ),
    ]
