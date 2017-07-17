#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json, os
from actstream.models import any_stream
    
from django.core import mail
from django.test import TestCase
from rest_framework.reverse import reverse

from miller.test import ApiMillerTestCase
from miller.models import Comment, Story, Document

dir_path = os.path.dirname(os.path.realpath(__file__))


# python manage.py test miller.test.test_api_caption.CaptionTest
class CaptionTest(ApiMillerTestCase):
  def setUp(self):
    super(CaptionTest, self).setUp()
    # add a few documents:
    # bulk create do not sending pre_save or post_save signal, the slug must be created manually
    self.documents = Document.objects.bulk_create([Document(
      title=u'Document %s' % k, 
      slug=u'document-%s' % k,
      owner=self.user_A,
      data={
        'title': u'Document %s' % k, 
        'description': u'This is the document %s' %k
      },
    ) for k in ['a', 'b', 'c', 'd']])


  def _test_extract_from_story(self):
    """
    For more complete tests on the Story model function, see miller.test.test_models_story.StoryTest
    """
    self.story_A.contents = json.dumps({
      'modules': [
        {
          'document': {
            'slug': 'document-a',
            'related':[
              {
                'slug': 'document-b',
              }
            ]
          }
        }
      ], 
      'overlay': {
        'background': {
          'slug': 'document-d'
        }
      }
    }, ensure_ascii=False)
    self.story_A.save()

    # verify the params with the Form.
    res = self.client_user_A.post('/api/caption/extract-from-story/%s/' % self.story_A.pk, {
      'key': 'slug',
    })

    self.assertEqual(res.status_code, 400)
    self.assertTrue(res.json()['parser'])

    # verify the (correct) response
    res = self.client_user_A.post('/api/caption/extract-from-story/%s/' % self.story_A.pk, {
      'key': 'slug',
      'parser': 'json'
    })
    resj = res.json()
    self.assertEqual(res.status_code, 200)
    self.assertTrue(resj['expected'])
    self.assertTrue(resj['results'])
    self.assertFalse(resj['missing'])
    
    # coherence of the results is tested in miller.test.test_models_story.StoryTest
    self.assertEqual(sorted(resj['expected']), [u'document-a', u'document-b', u'document-d'])

    # non-owner user cannot do much.
    res = self.client_user_B.post('/api/caption/extract-from-story/%s/' % self.story_A.pk, {
      'key': 'slug',
      'parser': 'json'
    })
    self.assertEqual(res.status_code, 404) # NOT FOUND ;)


  def test_suite(self):
    self._test_extract_from_story()
    self.cleanUp()
