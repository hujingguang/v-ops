# Generated by Django 3.1 on 2021-01-05 07:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deploymanage', '0028_appversionrecord_is_conflicted'),
    ]

    operations = [
        migrations.AlterField(
            model_name='deployapprecord',
            name='is_deleted',
            field=models.IntegerField(choices=[(0, '未删除'), (1, '已删除')], default=0, verbose_name='分支是否已删除'),
        ),
    ]
