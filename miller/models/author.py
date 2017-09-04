#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging, json

from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver

from miller import helpers
from miller.models import Profile

logger = logging.getLogger('miller')

orcid_regex = RegexValidator(regex=r'^[\d\-]+$', message="ORCID should contain only numbers and '-' sign")
    
def initial_data():
  return {
    'firstname': '',
    'lastname': ''
  }

class Author(models.Model):

  fullname    = models.TextField()
  affiliation = models.TextField(null=True, blank=True) # e.g Government and Politics, University of Luxembpourg
  metadata    = models.TextField(null=True, blank=True, default=json.dumps({ # deprecated
    'firstname': '',
    'lastname': ''
  }, indent=1))
  data        = JSONField(default=initial_data)

  orcid       = models.CharField(max_length=24, validators=[orcid_regex], blank=True) #if any
  slug        = models.CharField(max_length=140, unique=True, blank=True)
  user        = models.ForeignKey(User, related_name='authorship', blank=True, null=True, on_delete=models.CASCADE)


  @property
  def dmetadata(self):
    if not hasattr(self, '_dmetadata'):
      try:
        self._dmetadata  = json.loads(self.metadata)
      except Exception as e:
        self._dmetadata = {}
        logger.exception(e)
        return {}
      else:
        return self._dmetadata
      instance._dispatcher = True
    else:
      return self._dmetadata


  def asXMLContributor(self, contributorType='RelatedPerson'):
    """
    serialize as XML <contributor> for doi metadata 
    <contributors>
      <contributor contributorType="ProjectLeader">
      <contributorName>Starr, Joan</contributorName>
      <nameIdentifier schemeURI="http://orcid.org/" nameIdentifierScheme="ORCID">0000-0002-7285-027X</nameIdentifier>
      <affiliation>California Digital Library</affiliation>
      </contributor>
    </contributors>
    """
    cre = u"""
        <contributor contributorType="%(contributorType)s" >
          <contributorName>%(contributorName)s</contributorName>
          <givenName>%(givenName)s</givenName>
          <familyName>%(familyName)s</familyName>
          %(ORCID)s
          <affiliation>%(affiliation)s</affiliation>
        </contributor>
        """ % self.asDictContributor()

    return cre


  def asDictContributor(self, contributorType='RelatedPerson'):
    return {
        'contributorType': contributorType,
        'contributorName': u', '.join(filter(None, (self.data.get('lastname'),self.data.get('firstname')))),
        'givenName': self.data.get('firstname', ''),
        'familyName': self.data.get('lastname', ''),
        'ORCID': '' if not self.orcid else '<nameIdentifier schemeURI="http://orcid.org/" nameIdentifierScheme="ORCID">%s</nameIdentifier>'% self.orcid,
        'affiliation': self.affiliation if self.affiliation else ''
    }


  def asXMLCreator(self):
    """
    serialize as XML <creator> for doi metadata 
    """
    cre = u"""
        <creator>
          <creatorName>%(creatorName)s</creatorName>
          <givenName>%(givenName)s</givenName>
          <familyName>%(familyName)s</familyName>%(ORCID)s
          <affiliation>%(affiliation)s</affiliation>
        </creator>
        """ % self.asDictCreator()

    return cre


  def asDictCreator(self):
    """
    serialize as Dict <creator> for doi metadata preview (JSON api)
    """
    cre = {
      'creatorName': u', '.join(filter(None, (self.data.get('lastname'),self.data.get('firstname')))),
      'givenName': self.data.get('firstname', ''),
      'familyName': self.data.get('lastname', ''),
      'ORCID': '' if not self.orcid else '<nameIdentifier schemeURI="http://orcid.org/" nameIdentifierScheme="ORCID">%s</nameIdentifier>'% self.orcid,
      'affiliation': self.affiliation if self.affiliation else ''
    }
    return cre


  class Meta:
    app_label="miller"

  def __unicode__(self):
    return u' '.join(filter(None,[
      self.fullname, 
      '(%s)'%self.user.username if self.user else None,
      self.affiliation
    ]))

  def save(self, *args, **kwargs):
    if not self.pk and not self.slug:
      self.slug = helpers.get_unique_slug(self, self.fullname)
    super(Author, self).save(*args, **kwargs)


  def updatePublishedStories(self):
    num_stories = self.stories.filter(status='public').count()
    self.data.update({
      'num_stories': num_stories
    })
    self.save()

# create an author whenever a Profile is created.
@receiver(post_save, sender=Profile)
def create_author(sender, instance, created, **kwargs):
  if kwargs['raw']:
    return
  if created:
    fullname = u'%s %s' % (instance.user.first_name, instance.user.last_name) if instance.user.first_name else instance.user.username
    aut = Author(user=instance.user, fullname=fullname, data={
      'firstname': instance.user.first_name,
      'lastname': instance.user.last_name
    })
    aut.save()
    logger.debug('(user {pk:%s}) @post_save: author created.' % instance.pk)

