# Generated by Django 3.1 on 2021-02-02 04:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deploymanage', '0032_vmhostinfo_vm_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='vmhostinfo',
            name='is_inited',
            field=models.IntegerField(choices=[(0, '否'), (1, '是')], default=0, verbose_name='是否初始化'),
        ),
    ]
