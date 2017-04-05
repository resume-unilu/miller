#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, logging, json

from actstream import action

from miller import helpers

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import pre_delete, post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth.models import User



logger = logging.getLogger('miller.commands')

class Review(models.Model):
  """
  Due by
  """
  EDITING      = 'editing'
  DOUBLE_BLIND = 'double'
  TRANSPARENT  = 'open'

  CATEGORY_CHOICES = (
    (EDITING,      'editing'),
    (DOUBLE_BLIND, 'double blind'),
    (TRANSPARENT, 'open')
  )

  INITIAL   = 'initial'
  DRAFT     = 'draft'
  PRIVATE   = 'private'
  REFUSAL   = 'refusal'
  COMPLETED    = 'complete'
  BOUNCE    = 'bounce'
  PUBLIC    = 'public'

  STATUS_CHOICES = (
    (INITIAL,   'initial'),
    (DRAFT,     'draft'),
    (PRIVATE,   'private'),
    (PUBLIC,    'public'),
    (REFUSAL,   'refusal'),
    (BOUNCE,    'bounce'),
    (COMPLETED, 'complete')
  )

  # List of fields
  FIELDS = ('thematic','thematic_score','interest', 'interest_score', 'originality', 'originality_score', 'innovation', 'innovation_score', 'interdisciplinarity', 'interdisciplinarity_score', 'methodology_score', 'methodology', 'clarity', 'clarity_score', 'argumentation_score', 'argumentation',
      'structure_score','structure', 'references', 'references_score', 'pertinence','pertinence_score',)

  FIELDS_FOR_SCORE     = filter(lambda x: x.endswith('_score'), FIELDS)
  FIELDS_NOT_FOR_SCORE = filter(lambda x: not x.endswith('_score'), FIELDS)

  story       = models.ForeignKey('miller.Story', related_name='reviews', help_text="This shows only stories having status 'review' or 'editing'")
  assignee    = models.ForeignKey('auth.User', related_name='assigned_reviews', help_text="To include users in this list, add them to the groups 'editors' or 'reviewers'") # at least the first author, the one who owns the file.
  assigned_by = models.ForeignKey('auth.User', blank=True, null=True, related_name='dispatched_reviews', help_text="This has been automatically assigned.") # should be request.user in case of admin.

  category = models.CharField(max_length=8, choices=CATEGORY_CHOICES, default=EDITING) # e.g. 'actor' or 'institution'
  
  status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=INITIAL)

  due_date           = models.DateTimeField(null=True, blank=True)
  date_created       = models.DateTimeField(auto_now_add=True)
  date_last_modified = models.DateTimeField(auto_now=True)

  contents = models.TextField(default=json.dumps({
    'title': '',
    'text': ''
  }, indent=1),blank=True) # generic contents for the generic introduction? Is it ok?
  

  thematic = models.TextField(null=True, blank=True)
  thematic_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(5),
      MinValueValidator(0) # valid valus will then go from 1 to 5
    ]
  ) # Le tapuscrit se rattache-t-il aux thèmes abordés par le projet de recherche RESuME?
  interest = models.TextField(null=True, blank=True)
  interest_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(5),
      MinValueValidator(0) # valid valus will then go from 1 to 5
    ]
  ) # Le tapuscrit présente-t-il un intérêt pour la communauté-cible du projet RESuME?
  originality = models.TextField(null=True, blank=True)
  originality_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(5),
      MinValueValidator(0) # valid valus will then go from 1 to 5
    ]
  ) # Le sujet du tapuscrit se distingue-t-il par son innovation et son originalité?
  innovation = models.TextField(null=True, blank=True)
  innovation_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(5),
      MinValueValidator(0) # valid valus will then go from 1 to 5
    ]
  ) # Le tapuscrit apporte-t-il des éléments d’interprétation ou de compréhension nouveaux du sujet abordé?
  interdisciplinarity = models.TextField(null=True, blank=True)
  interdisciplinarity_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(5),
      MinValueValidator(0) # valid valus will then go from 1 to 5
    ]
  )# Le tapuscrit se distingue-t-il par son caractère interdisciplinaire?
  methodology = models.TextField(null=True, blank=True)
  methodology_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(5),
      MinValueValidator(0) # valid valus will then go from 1 to 5
    ]
  )# La méthodologie appliquée par l’auteur est-elle appropriée et justifiée au regard du sujet traité?
  clarity = models.TextField(null=True, blank=True)
  clarity_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(5),
      MinValueValidator(0) # valid valus will then go from 1 to 5
    ]
  ) # La problématique et les objectifs de recherche/d’analyse du tapuscrit sont-ils clairement exposés?
  argumentation = models.TextField(null=True, blank=True)
  argumentation_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(5),
      MinValueValidator(0) # valid valus will then go from 1 to 5
    ]
  ) # L’argumentation développée dans le tapuscrit est-elle convaincante au regard de la problématique retenue?
  structure = models.TextField(null=True, blank=True)
  structure_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(5),
      MinValueValidator(0) # valid valus will then go from 1 to 5
    ]
  )# La structure du tapuscrit, l’intitulé des différentes sections sont-ils signifiants?
  references = models.TextField(null=True, blank=True)
  references_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(5),
      MinValueValidator(0) # valid valus will then go from 1 to 5
    ]
  )#Les références citées en notes de bas de page sont-elles justifiées, pertinentes, actualisées?
  pertinence = models.TextField(null=True, blank=True)
  pertinence_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(5),
      MinValueValidator(0) # valid valus will then go from 1 to 5
    ]
  )# Les ressources documentaires sélectionnées contribuent-elles utilement à l’argumentation?

  score = models.IntegerField(null=True, blank=True) # this is normally autosaved.


  def __unicode__(self):
    return '%s:%s - reviewer:%s' % (self.category, self.story.title, self.assignee.username)


  def __init__(self, *args, **kwargs):
    super(Review, self).__init__(*args, **kwargs)
    if self.pk:
      self._original = {
        'assignee__pk': self.assignee.pk,
        'status': self.status
      }
  

  def send_email_to_assignee(self, template_name, extra={}):
    """
    send email to assignee
    """
    recipient = self.assignee.email
    context = {
      'username': self.assignee.username,
      'site_name': settings.MILLER_TITLE,
      'reviews_url': settings.MILLER_SETTINGS['host'] + '/login/?next=/reviews',
      'site_name': settings.MILLER_TITLE,
      'site_url':  settings.MILLER_SETTINGS['host']
    }
    # update with extra field according to email template.
    context.update(extra);

    if recipient:
      logger.debug('review {pk:%s} sending email to user {pk:%s}...' % (self.pk, self.assignee.pk))
      from templated_email import send_templated_mail
      send_templated_mail(template_name=template_name, from_email=settings.DEFAULT_FROM_EMAIL, recipient_list=[self.assignee.email], context=context)
        # from_email=settings.DEFAULT_FROM_EMAIL, 
    else:
      logger.debug('review {pk:%s} cannot send email to assignee, user {pk:%s} email not found!' % (self.pk, self.assignee.pk))
      

  def generate_report(self, doubleblind=True):
    """
    Genereate a markdown report (useful for sending email)
    """
    try:
      contents = json.loads(self.contents)['text']
    except Exception as e:
      contents = self.contents

    chunks = [
      'Review Report',
      '===',
      '',
      'date: %s' % self.date_created.isoformat(),
      'due date: %s' % self.due_date.isoformat(),
      'last modification date: %s' % self.date_last_modified.isoformat(),
      'category of review: %s' % self.category,
      '',
    ]

    if not doubleblind:
      chunks = chunks + [
         '---',
        u'authors: %s' % ', '.join('%s (%s)' % (aut.fullname, aut.user.username if aut.user else 'no username') for aut in instance.story.authors.all()),
        u'assignee: %s' % instance.assignee.username,
        u'assigned by: %s' % instance.assigned_by.username,
      ]

    chunks = chunks + [
      '---',
      u'final score: %s' % self.score,
      u'',
      u'score details:'
    ]

    for f in Review.FIELDS:
      chunks.append(u'- %s: %s' % (f, getattr(self, f)))
    
    chunks = chunks + [
      '---',
      contents,  
      '',
      u'final result: %s' % self.status
    ]

    return '\n'.join(chunks)

    

@receiver(pre_save, sender=Review)
def calculate_score(sender, instance, **kwargs):
  """
  Precalculate score according to SCORE_FIELD integer fields
  """
  if instance.pk:
    #print [getattr(instance, f) for f in Review.FIELDS_FOR_SCORE]
    instance.score = reduce(lambda x,y: (x if x is not None else 0)+(y if y is not None else 0), [getattr(instance, f) for f in Review.FIELDS_FOR_SCORE])
    logger.debug('review {pk:%s} @pre_save, total score: %s' % (instance.pk, instance.score))
    


@receiver(post_save, sender=Review)
def dispatcher(sender, instance, created, **kwargs):
  if created or (hasattr(instance, '_original') and instance._original['assignee__pk'] != instance.assignee.pk):
    logger.debug('review {pk:%s, category:%s} sending email to user {pk:%s}...' % (instance.pk, instance.category, instance.assignee.pk))
    try:
      instance.send_email_to_assignee(template_name='assignee_%s'%instance.category)
    except Exception as e:
      logger.exception(e)
    # else:
    #   logger.debug('review {pk:%s, category:%s} cannot send email to assignee, no settings.EMAIL_HOST present in loca_settings ...' %(instance.category, instance.pk))



# @receiver(post_save, sender=Review)
# def git_commit(sender, instance, created, **kwargs):
#   """
#   convenient function to commit the review
#   """
#   logger.debug('review {pk:%s} init git commit...' % self.pk)

#   path = instance.assignee.get_path()
  
#   f = codecs.open(path, encoding='utf-8', mode='w+')
#   f.write(instance.generate_report)
#   f.seek(0)
#   f.close()

  
#   author = Actor(self.owner.username, self.owner.email)
#   committer = Actor(settings.GIT_COMMITTER['name'], settings.GIT_COMMITTER['email'])

#   # commit if there are any differences
#   repo = Repo.init(settings.GIT_ROOT)

#   # add and commit JUST THIS FILE
#   #tree = Tree(repo=repo, path=self.owner.profile.get_path())
#   repo.index.add([self.owner.profile.get_path()])
#   c = repo.index.commit(message=u"saving %s" % self.title, author=author, committer=committer)


#   logger.debug('story {pk:%s} git commit done.' % self.pk)


