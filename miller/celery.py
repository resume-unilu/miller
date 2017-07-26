from __future__ import absolute_import, unicode_literals

import os
from celery import Celery
from django.conf import settings

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'miller.settings')

app = Celery('miller')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks()
