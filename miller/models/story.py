#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os,codecs

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils.text import slugify

from miller import helpers
from miller.models import Tag, Document

from simplemde.fields import SimpleMDEField


class Story(models.Model):
  DRAFT   = 'draft' # visible just for you
  SHARED  = 'shared' # share with specific user
  PUBLIC  = 'public' # everyone can access that.

  STATUS_CHOICES = (
    (DRAFT, 'draft'),
    (SHARED, 'shared'),
    (PUBLIC, 'public'),
  )

  short_url = models.CharField(max_length=22, default=helpers.create_short_url, unique=True)
  
  title     = models.CharField(max_length=500)
  slug      = models.CharField(max_length=140, unique=True, blank=True) # force the unicity of the slug (story lookup from the short_url)
  abstract  = models.CharField(max_length=500, blank=True, null=True)
  contents  = SimpleMDEField(verbose_name=u'mardown content',default='') # It will store the last markdown contents.

  date               = models.DateTimeField(blank=True, null=True) # date displayed (metadata)
  date_created       = models.DateTimeField(auto_now_add=True)
  date_last_modified = models.DateTimeField(auto_now=True)

  status    = models.CharField(max_length=10, choices=STATUS_CHOICES)

  owner     = models.ForeignKey(User); # at least the first author, the one who owns the file.
  authors   = models.ManyToManyField(User, related_name='authors', blank=True) # collaborators
  watchers  = models.ManyToManyField(User, related_name='watchers', blank=True) # collaborators
  documents = models.ManyToManyField(Document, related_name='documents', through='Caption', blank=True)

  tags      = models.ManyToManyField(Tag, blank=True) # tags

  # cover thumbnail, e.g. http://www.eleganzadelgusto.com/wordpress/wp-content/uploads/2014/05/Marcello-Mastroianni-for-Arturo-Zavattini.jpg
  cover = models.URLField(max_length=500, blank=True, null=True)

  # cover copyright or caption, markdown flavoured. If any
  cover_copyright = models.CharField(max_length=140, blank=True, null=True)

  # set the plural name and fix the default sorting order
  class Meta:
    ordering = ('-date_last_modified',)
    verbose_name_plural = 'stories'

  # get story path based on random generated shorten url
  def get_path(self):
    return os.path.join(self.owner.profile.get_path(), self.short_url+ '.md')
  
  def __unicode__(self):
    return '%s - by %s' % (self.title, self.owner.username)

  def save(self, *args, **kwargs):
    self.slug = slugify(self.title)
    super(Story, self).save(*args, **kwargs)


# create story file if it is not exists; if the story eists already, cfr the followinf post_save
@receiver(post_save, sender=Story)
def create_working_md(sender, instance, created, **kwargs):
  path = instance.get_path()
  if created:
    print 'create sroty'
    instance.authors.add(instance.owner)
    instance.save()
    
  f = codecs.open(path, encoding='utf-8', mode='w+')
  f.write(instance.contents)
  f.seek(0)
  f.close()

  from git import Repo, Commit, Actor, Tree

  author = Actor(instance.owner.username, instance.owner.email)
  committer = Actor(settings.GIT_COMMITTER['name'], settings.GIT_COMMITTER['email'])

  # commit if there are any differences
  repo = Repo.init(settings.GIT_ROOT)

  # add and commit JUST THIS FILE
  #tree = Tree(repo=repo, path=instance.owner.profile.get_path())
  repo.index.add([instance.owner.profile.get_path()])
  repo.index.commit(message=u"saving %s" % instance.title, author=author, committer=committer)


    
