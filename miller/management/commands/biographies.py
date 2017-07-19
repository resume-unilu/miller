#!/usr/bin/env python
# -*- coding: utf-8 -*-
# special tasks for biographical data
import logging
import pydash as pyd

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.cache import cache
from django.db import transaction

from miller.management.commands.task import Command as TaskCommand
from miller.management.commands import utils
from miller.models import Author, Document, Story, Profile, Tag

logger = logging.getLogger('console')


class Command(TaskCommand):
  """
  Usage sample: 
  python manage.py task snapshot --pk=991
  """
  help = 'A lot of tasks dealing with biographical data'
  

  available_tasks = (
    'bulk_import_gs_as_biographies',
    'bulk_import_dbpedia_for_biographies',
    'bulk_import_gs_as_biographies_activities'
  )


  def bulk_import_dbpedia_for_biographies(self, pk=None, **options):
   

    docs = Document.objects.filter(data__type='person', data__wiki_id__isnull=False)

    if pk:
      god = {'pk': pk} if pk.isdigit() else {'slug':pk}
      logger.debug('USING %s' % god)
      docs = Document.objects.filter(**god).filter(data__type='person', data__wiki_id__isnull=False)
    logger.debug('documents: %s' % docs.count())

    for doc in docs.iterator():
      logger.debug('document {slug:%s, wiki_id:%s}' % (doc.slug, doc.data['wiki_id']))
      
      if not doc.data['wiki_id']:
        logger.debug('skipping, BAD wiki_id.')
        continue

      contents = utils.dbpedia(wiki_id=doc.data['wiki_id'])

      #      doc.save()
      try:
        resource = contents['http://dbpedia.org/resource/%s' % doc.data['wiki_id']]
      except KeyError as e:
        logger.debug('skipping, wiki_id: %s gives empty results' % doc.data['wiki_id'])
        continue
      # print resource

      doc.data['thumbnail'] = pyd.get(resource.get('http://dbpedia.org/ontology/thumbnail'), '[0].value')
      doc.data['url']       = pyd.get(resource.get('http://xmlns.com/foaf/0.1/depiction'), '[0].value')

      if not doc.data['thumbnail'] and not doc.data['url']:
        logger.debug('skipping, no data need to be updated.')
        continue
      else:
        doc.data['provider_name'] = 'dbpedia'
        doc.data['provider_url']  = 'dbpedia.org' 

        logger.debug('thumbnail: %s' % doc.data['thumbnail'])
        logger.debug('imageurl: %s' % doc.data['url'])


      doc.save()
      #resource = pyd.get(contents, 'http://dbpedia.org/resource/%s' % doc.data['wiki_id'])
      #print resource
      #print pyd.get(contents, 'http://dbpedia.org/resource/%s.http://dbpedia.org/ontology/thumbnail'%doc.data['wiki_id'])
      
  

  def bulk_import_gs_as_biographies_activities(self, url=None, owner=None, sheet=None, **options):
    """
    usage:
    python -W ignore manage.py task bulk_import_gs_as_biographies_activities --url=<your url> --sheet=activities
    """
    rows, headers = utils.bulk_import_gs(url=url, sheet=sheet, use_cache=options['cache'], required_headers=['person_slug'])
    
    # group rows by person_slug
    people = pyd.group_by(rows, 'person_slug')
    #print people
    data_paths =  utils.data_paths(headers=headers) 
    #print data_paths
    # basic data structure based on headers column
    data_structure = {}

    for i, path, is_list in data_paths:
      utils.nested_set(data_structure, path, {})
    #print data_structure

    def mapper(d):
      #print d
      _d = {
        'sorting': pyd.get(d, u'data__activity__sorting', ''),
        'type': pyd.get(d, u'data__activity__type', ''),
        'description': {
          'en_US': pyd.get(d, u'data__activity__description__en_US', ''),
          'fr_FR': pyd.get(d, u'data__activity__description__fr_FR', '')
        },
        'date': {
          'en_US': pyd.get(d, u'data__activity__date__en_US', ''),
          'fr_FR': pyd.get(d, u'data__activity__date__fr_FR', '')
        },
        'start_date':  pyd.get(d, u'data__activity__start_date'),
        'end_date':  pyd.get(d, u'data__activity__end_date')
      }
      return _d



    for slug, activities in people.iteritems():
      logger.debug('adding %s activities to document {slug:%s}' % (len(activities), slug))
      
      doc = Document.objects.get(slug=slug,type=Document.ENTITY)

      doc.data['activities'] = map(mapper, activities)
      doc.save()

      #map(activities)
      


  def bulk_import_gs_as_biographies(self, url=None, owner=None, sheet=None, **options):
    """
    usage:
    python -W ignore manage.py task bulk_import_gs_as_biographies --owner=<your username> --url=<your url> --sheet=people
    """
    logger.debug('loading %s' % url)
    # print owner, options
    
    owner = Profile.objects.filter(user__username=owner).first()
    if not owner:
      raise Exception('specify a **valid** miller username with the --owner parameter.')
    
    logger.debug('with owner: %s' % owner)

    biotag = Tag.objects.get(category=Tag.WRITING, slug='biography')


    rows, headers = utils.bulk_import_gs(url=url, sheet=sheet, use_cache=options['cache'], required_headers=['slug', 'type'])
    
    # create ---stories---
    logger.debug('saving stories with related document...')
    for i, row in enumerate(rows):
      if not row['slug'] or not row['type'] or not row['title']:
        logger.debug('line %s: empty "slug", skipping.' % i)
        continue

      _slug = row.get('slug', '')
      _type = row.get('type', '')

      story, created = Story.objects.get_or_create(slug=_slug, defaults={
        'owner': owner.user,
        'title': row.get('title', '')
      })
      # print story.slug, not story.title, created
      if not story.title:
        story.title = row.get('title', '')

      if not story.abstract:
        story.abstract = '\n'.join(filter(None, [
          row.get('data__description__en_US', ''),
          row.get('data__date__en_US','')
        ])).strip()
      # add birthdate to abstract
      #story.data['abstract']['en_US'] = 
     

      #print row
      #if not story.data or not 'title' in story.data:
      story.data.update({
        'title': {
          'en_US': '\n'.join(filter(None,[row.get('title', '')]))
        },
        'abstract': {
          'en_US': '\n'.join(filter(None, [
            row.get('data__description__en_US', ''),
            row.get('data__date__en_US','')
          ])).strip()
        }
      })
      #print story.title, row['title'].strip()

      if not story.data.get('title').get('en_US', None):
        story.data['title']['en_US'] = row.get('title', '')

      if not story.data.get('abstract').get('en_US', None):
        story.data['abstract']['en_US'] = row.get('data__description__en_US', '')
      
      # create or get a document of type 'entity'
      doc, dcreated = Document.objects.get_or_create(slug=_slug, type=Document.ENTITY, defaults={
        'owner': owner.user
      })

      if not doc.title:
        doc.title = row['title'].strip()

      logger.debug('- with cover document {slug:%s, type:%s, created:%s}' % (doc.slug, doc.type, dcreated))
      
      story.tags.add(biotag)
      story.covers.add(doc)
      story.authors.add(owner.user.authorship.first())
      story.save()

      logger.debug('ok - story {slug:%s, created:%s} saved' % (story.slug, created))
    logger.debug('updating document data...')
    self.bulk_import_gs_as_documents(url=url, sheet=sheet, use_cache=True, required_headers=['slug', 'type'])
    