# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-09-12 14:32
from __future__ import unicode_literals

from django.db import migrations, models
import miller.helpers


class Migration(migrations.Migration):

    dependencies = [
        ('miller', '0021_auto_20160907_0712'),
    ]

    operations = [
        migrations.AlterField(
            model_name='document',
            name='short_url',
            field=models.CharField(db_index=True, default=miller.helpers.create_short_url, max_length=22, unique=True),
        ),
    ]
