# Generated by Django 3.1 on 2021-02-01 08:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deploymanage', '0031_vmhostinfo'),
    ]

    operations = [
        migrations.AddField(
            model_name='vmhostinfo',
            name='vm_id',
            field=models.CharField(max_length=64, null=True, verbose_name='虚拟机id'),
        ),
    ]
