# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-07 15:34
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('miller', '0005_auto_20160407_1527'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='caption',
            options={'ordering': ['-date_created'], 'verbose_name_plural': 'captions'},
        ),
    ]
