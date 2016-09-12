#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os,codecs, json, logging

from BeautifulSoup import BeautifulSoup

from django.conf import settings
from django.db import models
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from django.utils.text import slugify

from jsonfield import JSONField

from markdown import markdown

from miller import helpers
from miller.models import Tag, Document

from simplemde.fields import SimpleMDEField


logger = logging.getLogger('miller')

class Story(models.Model):
  DRAFT   = 'draft' # visible just for you
  SHARED  = 'shared' # share with specific user
  PUBLIC  = 'public' # everyone can access that.

  STATUS_CHOICES = (
    (DRAFT, 'draft'),
    (SHARED, 'shared'),
    (PUBLIC, 'public'),
  )

  short_url = models.CharField(max_length=22, db_index=True, default=helpers.create_short_url, unique=True)
  
  title     = models.CharField(max_length=500)
  slug      = models.CharField(max_length=140, unique=True, blank=True) # force the unicity of the slug (story lookup from the short_url)
  abstract  = models.CharField(max_length=500, blank=True, null=True)
  contents  = SimpleMDEField(verbose_name=u'mardown content',default='') # It will store the last markdown contents.
  metadata  = JSONField(default=json.dumps({'title':{'en':'', 'fr':''}, 'abstract':{'en':'', 'fr':''}})) # it will contain, JSON fashion


  date               = models.DateTimeField(blank=True, null=True) # date displayed (metadata)
  date_created       = models.DateTimeField(auto_now_add=True)
  date_last_modified = models.DateTimeField(auto_now=True)

  status    = models.CharField(max_length=10, choices=STATUS_CHOICES)

  owner     = models.ForeignKey(User); # at least the first author, the one who owns the file.
  authors   = models.ManyToManyField(User, related_name='authors', blank=True) # collaborators
  watchers  = models.ManyToManyField(User, related_name='watchers', blank=True) # collaborators
  documents = models.ManyToManyField(Document, related_name='documents', through='Caption', blank=True)
  
  # the leading document(s), e.g. an interview
  covers = models.ManyToManyField(Document, related_name='covers', blank=True)

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

  # store into the whoosh index
  def store(self, ix=None):
    if ix is None:
      ix = helpers.get_whoosh_index()
    writer = ix.writer()
    writer.update_document(
      title = self.title,
      path = u"%s"%self.short_url,
      content =  u"\n".join(BeautifulSoup(markdown(u"\n".join(filter(None,[self.title, self.abstract, self.contents])), extensions=['footnotes'])).findAll(text=True)),
      tags = u",".join([u'%s'%t.name for t in self.tags.all()]),
      classname = u"story")
    writer.commit()

  def save(self, *args, **kwargs):
    if not self.id and not self.slug:
      slug = slugify(self.title)
      slug_exists = True
      counter = 1
      self.slug = slug
      while slug_exists:
        try:
          slug_exits = Story.objects.get(slug=slug)
          if slug_exits:
              slug = self.slug + '-' + str(counter)
              counter += 1
        except Story.DoesNotExist:
          self.slug = slug
          break

    try:
      metadata = json.loads(self.metadata)
      
      if 'title' not in metadata:
        metadata['title'] = {}
      if 'abstract' not in metadata:
        metadata['abstract'] = {}

      for default_language_code, label, language_code in settings.LANGUAGES:
        logger.debug('  lang:%s' % language_code)
        if language_code not in metadata['title']:
          metadata['title'][language_code] = self.title

        if language_code not in metadata['abstract']:
          metadata['abstract'][language_code] = self.abstract

      logger.debug('metadata %s' % metadata)
      self.metadata = json.dumps(metadata)
    except Exception as e:
      logger.exception(e)

    # reconcile metadata with the current languages

    super(Story, self).save(*args, **kwargs)

# store in whoosh
@receiver(post_save, sender=Story)
def store_working_md(sender, instance, created, **kwargs):
  instance.store()


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


    
