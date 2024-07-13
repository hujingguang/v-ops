# Generated by Django 3.1 on 2020-11-26 01:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deploymanage', '0007_deployapprecord_description'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deployapprecord',
            name='publish_status',
            field=models.IntegerField(choices=[(0, '未上线'), (1, '已上线'), (2, '上线中')], default=0, verbose_name='上线状态'),
        ),
    ]