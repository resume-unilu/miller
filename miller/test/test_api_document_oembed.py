#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json, os, logging
from actstream.models import any_stream
    
from django.core import mail
from django.test import TestCase
from rest_framework.reverse import reverse

from miller.test import ApiMillerTestCase
from miller.models import Comment, Story

dir_path = os.path.dirname(os.path.realpath(__file__))

logger = logging.getLogger('console')

URL_EUPDF    = "https://ec.europa.eu/info/sites/info/files/file_import/10_fr_scp_en_4.pdf"
URL_EUPRESS  = "http://europa.eu/rapid/press-release_SPEECH-17-723_en.htm"
URL_EUHTML   = "http://www.europarl.europa.eu/news/en/news-room/20170228IPR64287/future-of-the-eu-meps-discuss-five-scenarios-set-out-by-jean-claude-juncker"
URL_EUDATA   = "http://ec.europa.eu/eurostat/data/database"
URL_EURLEX   = "http://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A12012M050"
URL_LEMONDE  = "http://www.lemonde.fr/elections-legislatives-2017/article/2017/05/12/liste-de-la-republique-en-marche-aux-legislatives-la-colere-de-francois-bayrou_5126457_5076653.html"
URL_BRUEGEL  = "http://bruegel.org/wp-content/uploads/2017/02/Bruegel_Policy_Brief-2017_01-090217.pdf"
URL_EURACTIV = "http://www.euractiv.com/section/future-eu/news/junckers-real-scenario-is-multi-speed-europe/"
URL_FLICKR   = "https://www.flickr.com/photos/stefanbarna/25903441043/in/dateposted/"


# python manage.py test miller.test.test_api_document_oembed.DocumentOembedTest
class DocumentOembedTest(ApiMillerTestCase):

  
  def _test_404_oembed(self):
    logger.info('_test_404_oembed')
    res = self.client_anonymous.get('/api/document/oembed/?url=%s'%URL_EUPDF)
    self.assertEqual(res.status_code, 403)

  def _test_oembed(self):
    logger.info('_test_oembed')
    res = self.client_user_A.get('/api/document/oembed/?url=%s'%URL_EUPDF)
    self.assertEqual(res.status_code, 200)
    self.assertEqual(res.json().get('url'), URL_EUPDF)
    self.assertEqual(res.json().get('provider_url'), u'ec.europa.eu')


  def test_suite(self):
    self._test_404_oembed()
    self._test_oembed()
    self.cleanUp()