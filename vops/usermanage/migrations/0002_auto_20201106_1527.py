# Generated by Django 3.1 on 2020-11-06 07:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('usermanage', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='permission',
            options={'permissions': (('menu_dashboard', '菜单 Dashboard'), ('menu_system_configure', '菜单 系统配置'))},
        ),
    ]