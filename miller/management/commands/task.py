#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Tasks on models
import os, logging, json, re

from miller.helpers import get_whoosh_index
from miller.models import Document, Story

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger('miller.commands')


class Command(BaseCommand):
  """
  Usage sample: 
  python manage.py task snapshot --pk=991
  """
  help = 'Initialize the JSON field metadata for Story instances'
  

  available_tasks = (
    'noembed',
    'snapshot', # require document pk, e.g python manage.py task snapshot --pk=991
    'snapshots', # handle pdf snapshot, python manage.py task snapshots
    'snapshots404',
    'cleanbin',
    'update_whoosh',
    'update_localisation',
    'update_localisation_gs'
  )


  def add_arguments(self, parser):
    parser.add_argument('taskname')
    # Named (optional) arguments
    parser.add_argument(
        '--pk',
        dest='pk',
        default=False,
        help='primary key of the instance',
    )

  def handle(self, *args, **options):
    if options['taskname'] in self.available_tasks:
      getattr(self, options['taskname'])(**options)
    else:
      logger.debug('command NOT FOUND, tasks availables: ["%s"]' % '","'.join(self.available_tasks))
    logger.debug('command finished.')
  
  
  def update_localisation_gs(self,  **options):
    """ 
    load the csv specified in MILLER_LOCALISATION_TABLE_GOOGLE_SPREADSHEET, if any provided.
    """
    url = settings.MILLER_LOCALISATION_TABLE_GOOGLE_SPREADSHEET
    # something like https://docs.google.com/spreadsheets/d/{yourid}/edit#gid=0
    if not url:
      raise Exception('no google spreadsheet link in settings.MILLER_LOCALISATION_TABLE_GOOGLE_SPREADSHEET')
    
    print url

    m = re.match(r'https://docs.google.com/spreadsheets/d/([^/]*)', url)
    if not m:
      raise Exception('bad url in settings.MILLER_LOCALISATION_TABLE_GOOGLE_SPREADSHEET')
    import requests, StringIO
    import unicodecsv as csv
    response = requests.get('https://docs.google.com/spreadsheets/d/%s/export?format=csv' % m.group(1), stream=True)
    # print response.content
    # rows = csv.DictReader(StringIO.StringIO(response.content), encoding='utf-8', delimiter='\t')
    if response.status_code != 200:
      raise Exception('bad response for settings.MILLER_LOCALISATION_TABLE_GOOGLE_SPREADSHEET')
    # for row in rows:
    #   print row
    logger.debug('writing csv file at settings.MILLER_LOCALISATION_TABLE:%s', settings.MILLER_LOCALISATION_TABLE)
    with open(settings.MILLER_LOCALISATION_TABLE, 'wb') as f:
      for chunk in response.iter_content(chunk_size=1024): 
        if chunk: # filter out keep-alive new chunks
          f.write(chunk)
    
    logger.debug('now updating localisation...')
    self.update_localisation(**options)

  def update_localisation(self,  **options):
    """ 
    load the csv specified in MILLER_LOCALISATION_TABLE
    """
    logger.debug('looking for the csv file at settings.MILLER_LOCALISATION_TABLE: %s'%settings.MILLER_LOCALISATION_TABLE)
    import unicodecsv as csv
    
    with open(settings.MILLER_LOCALISATION_TABLE) as f:
      rows = csv.DictReader(f, encoding='utf-8')
      translations = {}
      for row in rows:
        for lang, t, language_code in settings.LANGUAGES:
          if not language_code in translations:
            translations[language_code] = {}
          
          translations[language_code].update({
            row[u'KEY']: row[u'en_US'] if not row[language_code] else row[language_code]
          })
      #print translations
      for language_code, value in translations.iteritems():
        print language_code
        localename = os.path.join(os.path.dirname(settings.MILLER_LOCALISATION_TABLE), 'locale-%s.json' % language_code)
          
        with open(localename, "w") as wtf:
          logger.debug('creating: %s'%localename)
          wtf.write(json.dumps(translations[language_code],indent=2))

            #print row
    pass

  def update_whoosh(self,  **options):
    logger.debug('looking for a whoosh index')
    ix = get_whoosh_index(force_create=True)
    logger.debug('whoosh index available! Updating ...')
    
    stories = Story.objects.all()

    # # The `iterator()` method ensures only a few rows are fetched from
    # # the database at a time, saving memory.
    for story in stories.iterator():
      logger.debug('task: update_whoosh for story {pk:%s}' % story.pk)
      try:
        story.store(ix=ix)
      except Exception as e:
        logger.exception(e)
        break
      else:
        logger.debug('task: update_whoosh for story {pk:%s} success' % story.pk)
      

    docs = Document.objects.all()

    # The `iterator()` method ensures only a few rows are fetched from
    # the database at a time, saving memory.
    for doc in docs.iterator():
      logger.debug('task: update_whoosh for doc {pk:%s}...' % doc.pk)
      try:
        doc.store(ix=ix)
      except Exception as e:
        logger.exception(e)
        break
      else:
        logger.debug('task: update_whoosh for doc {pk:%s} success' % doc.pk)
    

  def noembed(self, **options):
    logger.debug('task: noembed!')
    if not options['pk']:
      raise Exception('--pk not found')
    
    logger.debug('task: noembed for {document:%s}' % options['pk'])

    doc = Document.objects.get(pk=options['pk'])
    try:
      doc.noembed()
      doc.save()
    except Exception as e:
      logger.exception(e)


  def snapshot(self, **options):
    logger.debug('task: snapshot!')
    if not options['pk']:
      raise Exception('--pk not found')
    
    logger.debug('task: snapshot for {document:%s}' % options['pk'])

    doc = Document.objects.get(pk=options['pk'])
    try:
      doc.fill_from_url()
      doc.create_snapshot()
      doc.save()
    except Exception as e:
      logger.exception(e)

  def snapshots(self, **options):
    logger.debug('task: snapshots!')

    docs = Document.objects.all()

    # The `iterator()` method ensures only a few rows are fetched from
    # the database at a time, saving memory.
    for doc in docs.iterator():
      logger.debug('task: snapshots for {document:%s}' % doc.id)
      try:
        doc.fill_from_url()
        doc.create_snapshot()
        doc.save()
      except Exception as e:
        logger.exception(e)


  def snapshots404(self, **options):
    """
    Find snapshots giving 404 so that we know what need to be fixed.
    """
    logger.debug('task: find 404 snapshots!')

    docs = Document.objects.exclude(url__isnull=True).filter(mimetype='application/pdf')
    logger.debug('  looking for application/pdf on %s / %s documents.' % (docs.count(), Document.objects.all().count()))
    # The `iterator()` method ensures only a few rows are fetched from
    # the database at a time, saving memory.
    for doc in docs.iterator():
      if not doc.snapshot or not os.path.exists(doc.snapshot.path):
        logger.debug('task: snapshot missing for {document:%s}' % doc.id)
      # try:
      #   doc.fill_from_url()
      #   doc.create_snapshot()
      #   doc.save()
      # except Exception as e:
      #   logger.exception(e)

    # having snapshot. Do file exists?
    # docs = Document.objects.exclude(snapshot__isnull=True)
    # for doc in docs.iterator():
    #   os.path.exists(doc.snapshot.path)

  #cleaning story.DELETED older than 2 months
  def cleanbin(self, **options):
    logger.debug('task: cleanbin')
      
