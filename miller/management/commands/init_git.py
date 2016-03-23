#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from git import Repo

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from miller.models import Story


class Command(BaseCommand):
  help = 'Initialize git in the path specified as settings.GIT_ROOT'

  def add_arguments(self, parser):
    pass

  def handle(self, *args, **options):
    if not os.path.exists(settings.GIT_ROOT):
      os.makedirs(settings.GIT_ROOT)
    print settings.GIT_ROOT, 'created'


    repo = Repo.init(settings.GIT_ROOT, bare=True)
    