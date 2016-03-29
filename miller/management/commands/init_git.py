#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from git import Repo, Commit

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from miller.models import Story, Profile


class Command(BaseCommand):
  help = 'Initialize git in the path specified as settings.GIT_ROOT'

  def add_arguments(self, parser):
    pass

  def handle(self, *args, **options):
    
    if not os.path.exists(settings.GIT_ROOT):
      os.makedirs(settings.GIT_ROOT)
      print settings.GIT_ROOT, 'created'
    
    # repo is the new Repo    
    repo = Repo.init(settings.GIT_ROOT)

    # users/ folder where md files will be stored.
    userspath  = os.path.join(settings.GIT_ROOT, 'users')

    if not os.path.exists(userspath):
      os.makedirs(userspath)

    # create appropriate directories for the existing users
    profiles = Profile.objects.all()
    for p in profiles:
      userpath = os.path.join(userspath, p.short_url)
      if not os.path.exists(userpath):
        os.makedirs(userpath)

    # get untracked files
    print repo.untracked_files

    # add untracked files
    if len(repo.untracked_files) > 0:
      repo.index.add(repo.untracked_files)
      repo.index.commit("Fresh start.")
    else:
      print "nothing to add, git ready"

   