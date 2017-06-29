#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, json
from django.conf import settings
from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from miller import helpers
from miller.models import Document


dir_path = os.path.dirname(os.path.realpath(__file__))

# python manage.py test miller.test.test_models_document.DocumentTest
class DocumentTest(TestCase):

  def setUp(self):
    self.user = User.objects.create_user(
      username='test-user-profile', 
      email='jacob@jacob', 
      password='top_secret')
    

  def _test_create(self):
    self.doc = Document(
      title=u'The happy story of the Promo', 
      url='http://ec.europa.eu/health/files/eudralex/vol-1/reg_2016_161/reg_2016_161_en.pdf',
      owner=self.user,
      data={
        "html": "original content here", 
        "title":"The happy story of the Promo", 
        "description":"The happy story of the Turtle."
      },
      locked = True
    )
    self.doc.save()
    self.doc.refresh_from_db()
    self.assertEqual('%s'%self.doc.search_vector, "'happy':2A,8B 'of':4A,10B 'promo':6A 'story':3A,9B 'the':1A,5A,7B,11B 'turtle':12B")
    self.assertEqual(self.doc.slug, 'the-happy-story-of-the-promo')
    self.assertEqual(self.doc.locked, True)
    
  def _test_fill_from_url(self):
    self.doc.fill_from_url()
    self.assertEqual('application/pdf', self.doc.mimetype)
    self.doc.create_snapshot()
    self.assertTrue(os.path.exists(self.doc.attachment.path)) # and should have a valid attachment


  def _test_fill_from_metadata(self):
    _doc  = Document(
      title=u'Bibtex parsing', 
      owner=self.user,
      data={"html": "new content here", "bibtex":"@ARTICLE {article,\n    author  = \"Daniele Guido\",\n    title   = \"Titolo\",\n    journal = \"Journal\",\n    year    = \"2016\"\n}"}
    )

    _doc.save()
    self.assertEqual(_doc.data['title'], u'Bibtex parsing')
    self.assertEqual(_doc.data['details']['bibtex']['author'], u'Daniele Guido')
    # since there is a bibtex field, fill_from_metadata() should e called correctly
    

  def _test_create_duplicated_url(self): 
    _doc = Document(
      title=u'The happy story of the Promo', 
      url='http://ec.europa.eu/health/files/eudralex/vol-1/reg_2016_161/reg_2016_161_en.pdf',
      owner=self.user,
      data={"html": "new content here"}
    )
    _doc.save()
    self.assertEqual(_doc.pk, self.doc.pk)
    # but content has changed since ...
    self.assertEqual(_doc.contents, self.doc.contents)
    # lock doc
    self.doc.locked = False
    self.doc.save()

    __doc = Document(
      title=u'The happy story of the Promo', 
      url='http://ec.europa.eu/health/files/eudralex/vol-1/reg_2016_161/reg_2016_161_en.pdf',
      owner=self.user,
      data={"html": "very new content here"}
    )
    __doc.save()
    self.assertEqual(__doc.pk, self.doc.pk)
    #self.assertEqual(self.doc.contents, _doc.contents)
    # the id shouldbe equal to the doc id
    print 'and that\'s it!'


  def _test_createwithattachment(self):
    from django.core import files
    filename = os.path.join(settings.BASE_DIR, 'miller/test', 'unilu.png')
    with open(filename) as f:
      
      _doc = Document(
        title=u'The happy story of the Promo, with avery very long title this time. How can Miller create a good slug for this?', 
        owner=self.user,
        data={"html": "original content here"},
        locked = True,
        mimetype='image/png',
        type= Document.IMAGE
      )
      # this launch instance.save()
      _doc.attachment.save(os.path.basename(filename), files.images.ImageFile(f), save=True)
      # print 'saved'
      # _doc.save()
      # should truncate slugs
      self.assertEqual(_doc.slug, 'the-happy-story-of-the-promo-with-avery-very-long-title-this-time-ho')
      self.assertEqual(_doc.locked, True)
      _doc.delete()


  #@todo check if shapshot and attachments have been deteted
  def _test_delete(self):
    self.doc.delete()
    # self.assertFalse(os.path.exists(path))

    
  def _test_delete_user(self):
    path = self.user.profile.get_path()
    self.user.delete()
    self.assertFalse(os.path.exists(path))
   
    
  def test_suite(self):
    self._test_create()
    self._test_createwithattachment()
    self._test_fill_from_url()
    self._test_fill_from_metadata()
    self._test_create_duplicated_url()
    self._test_delete();
    self._test_delete_user();