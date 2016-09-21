#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, json
from miller import helpers

dir_path = os.path.dirname(os.path.realpath(__file__))

#
#  test stopwords and pattern chunking.
#  python manage.py test miller.test.test_zotero.ZoteroTest --testrunner=miller.test.NoDbTestRunner
#
from django.test import TestCase
from django.conf import settings

class ZoteroTest(TestCase):
  def test_connection(self):
    print 'ok'

    created, collection, zotero = helpers.get_or_create_zotero_collection(settings.ZOTERO_IDENTITY_NAME)
    self.assertEqual(collection['data']['name'], settings.ZOTERO_IDENTITY_NAME)
    helpers.fill_zotero_collection(filename=os.path.join(dir_path, 'test_zotero.rdf'), collection=collection, zotero=zotero)
    # 
    # zot.create_collection([{
    #   'name': 'username library'
    # }])

    # for item in zot.collections():
    #   print item