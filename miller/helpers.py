#!/usr/bin/env python
# -*- coding: utf-8 -*-
import shortuuid, os

"""
Helpers.

usage sample:

  import miller.helpers

  print helpers.echo()

"""

def create_short_url(): 
  return shortuuid.uuid()[:7]


def get_whoosh_index():
  from django.conf import settings
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


def search_whoosh_index(query):
    from whoosh.qparser import QueryParser
    from whoosh.query import Term, Or
    ix = get_whoosh_index()
    parser = QueryParser("content", ix.schema)

    q = parser.parse(query)
    res = []
    # restrict_q = Or([Term("path", u'%s' % d.id) for d in qs])

    with ix.searcher() as searcher:
      results = searcher.search(q, limit=10, terms=True)
      
      for hit in results:
        res.append({
          'title': hit['title'],
          'id': hit['path'],
          'highlights': hit.highlights("content", top=5)
        })
      

    return res 
