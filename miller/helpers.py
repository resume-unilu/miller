#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.conf import settings
from pyzotero import zotero

import shortuuid, os, json, logging

logger = logging.getLogger('miller')

"""
Helpers.

usage sample:

  import miller.helpers

  print helpers.echo()

"""

def create_short_url(): 
  return shortuuid.uuid()[:7]


def get_whoosh_index():
  from whoosh.index import create_in, exists_in, open_dir
  from whoosh.fields import Schema, TEXT, KEYWORD, ID, STORED
    
  schema = Schema(title=TEXT(stored=True), path=ID(unique=True, stored=True), content=TEXT(stored=True), tags=KEYWORD, classname=KEYWORD)
    
  if not os.path.exists(settings.WHOOSH_ROOT):
    os.mkdir(settings.WHOOSH_ROOT)
  
  if not exists_in(settings.WHOOSH_ROOT):
    index = create_in(settings.WHOOSH_ROOT, schema)
  else:
    index = open_dir(settings.WHOOSH_ROOT)
  return index


def search_whoosh_index(query, *args, **kwargs):
    from whoosh.qparser import QueryParser
    from whoosh.query import Term, And
    ix = get_whoosh_index()
    parser = QueryParser("content", ix.schema)
    # user query
    q = parser.parse(query)

    print kwargs
    allow_q = And([Term(key, value) for key, value in kwargs.iteritems()])
    print allow_q
    # parse remaining args
    res = []
    # restrict_q = Or([Term("path", u'%s' % d.id) for d in qs])

    with ix.searcher() as searcher:
      results = searcher.search(q, filter=allow_q, limit=10, terms=True)
        
      for hit in results:
        res.append({
          'title': hit['title'],
          'short_url': hit['path'],
          'highlights': hit.highlights("content", top=5)
        })
      
    return res 


# fill a dictionary with metadata according to the languages specified in settings.py file
def fill_with_metadata(instance, fields=(u'title',u'abstract')):
  metadata = instance.metadata if type(instance.metadata) is dict else json.loads(instance.metadata)
  for field in fields:
    if field not in metadata:
      metadata[field] = {}

    for default_language_code, label, language_code in settings.LANGUAGES:
      if language_code not in metadata[field]:
        print "value", getattr(instance, field, u'')
        metadata[field][language_code] = getattr(instance, field, u'')

  metadata = json.dumps(metadata)
  return metadata


# Our starting point for zotero related stuffs.
# for a given username, get or create the proper zotero collection.
# Return created<bool>, collection<Collection>, zotero<Zotero>
def get_or_create_zotero_collection(username):
  if not hasattr(settings, 'ZOTERO_IDENTITY'):
    logger.warn('no settings.ZOTERO_IDENTITY found')
    return
  try:
    zot = zotero.Zotero(settings.ZOTERO_IDENTITY, 'user', settings.ZOTERO_API_KEY)
    colls = zot.all_collections()
  except:
    logger.exception('unable to get zotero collections, zotero id: %s, zotero key: %s' % (settings.ZOTERO_IDENTITY, settings.ZOTERO_API_KEY))
    return False, None, None

  # get collection by username (let's trust django username :D)
  for coll in colls:
    if coll['data']['name'] == username:
      return False, coll, zot
  
  # create collection
  collreq = zot.create_collection([{
    'name': username
  }])
  coll = json.loads(collreq)
  if 'successful' in coll:
    # print coll['successful']
    return True, coll['successful']['0'], zot

  logger.warn('unable to create collection, got %s' %collreq)
  return False, None, zot


# filename should be a valid zotero RDF
def fill_zotero_collection(filename, collection, zotero):
  if not zotero:
    logger.warn('no zotero instance found, cfr get_or_create_zotero_collection')
    return
  pass