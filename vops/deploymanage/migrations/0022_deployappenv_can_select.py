# Generated by Django 3.1 on 2020-12-04 06:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deploymanage', '0021_deployapppublishrecord_release_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='deployappenv',
            name='can_select',
            field=models.IntegerField(default=1, null=True, verbose_name='环境是否可选'),
        ),
    ]
