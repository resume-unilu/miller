#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, json
from miller import helpers

#
#  test stopwords and pattern chunking.
#  python manage.py test miller.test.test_zotero.ZoteroTest --testrunner=miller.test.NoDbTestRunner
#
from django.test import TestCase
from django.conf import settings

class ZoteroTest(TestCase):
  def test_connection(self):
    print 'ok'

    created, collection = helpers.get_or_create_zotero_collection(settings.ZOTERO_IDENTITY_NAME)
    print 'done', created

    self.assertEqual(collection['data']['name'], settings.ZOTERO_IDENTITY_NAME)
    print json.dumps(collection, sort_keys=True,indent=4)

    # 
    # zot.create_collection([{
    #   'name': 'username library'
    # }])

    # for item in zot.collections():
    #   print item