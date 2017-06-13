# -*- coding: utf-8 -*-
# Add pg_trigram extension. This requires PostgresQL user to be superuser
# `ALTER USER resume WITH SUPERUSER;` 
# and DO NOT FORGET TO user role when the migration is done.
# `ALTER USER myuser WITH NOSUPERUSER`
from __future__ import unicode_literals

from django.db import migrations

from django.contrib.postgres.operations import TrigramExtension, UnaccentExtension


class Migration(migrations.Migration):

    dependencies = [
        ('miller', '0082_auto_20170607_1149'),
    ]

    operations = [
        TrigramExtension(),
        UnaccentExtension()
    ]
