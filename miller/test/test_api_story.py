#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json,os
from actstream.models import any_stream
from django.test import TestCase
from miller.test import ApiMillerTestCase
from miller.models import Comment

dir_path = os.path.dirname(os.path.realpath(__file__))


# python manage.py test miller.test.test_api_story.StoryTest
class StoryTest(ApiMillerTestCase):

  def test_story_list(self):
    response = self.client_user_A.get('/api/story/%s/' % self.story_A.slug)
    self.assertEqual(response.json()['title'], self.story_A.title)

    response = self.client_user_A.get('/api/story/')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.json()['count'] > 0, True)

  def test_create_from_docx(self):
    # should create a doc with the right content.
    with open(os.path.join(dir_path, 'test.docx'),'r') as docx:
      # The user should be the owner as well.
      response = self.client_user_A.post('/api/story/', {'source': docx, 'title':'This is a sad old story'}, format='multipart')
      #print 'arrrrrgggggg', response.status_code
      self.assertEqual(response.status_code, 201)
      #print response
      response_json = json.loads(response.content)
      self.assertEqual(response_json[u'slug'], u'this-is-a-sad-old-story')
      self.assertEqual(response_json[u'contents'], u"## La compétitivité européenne :\\\ncompétition, coopération, solidarité\n\nVersion : 30 mai 2016\n\n### 1 L’exigence d’un engagement total\n\nLa compétitivité est une obsession[^1].\n\n[^1]: Krugman, Paul. Competitiveness : A Dangerous Obsession. *Foreign\n    Affairs*, mars-avril 1994, vol. 73, n°2, pp. 28-44 ; pour une\n    critique similaire du « diktat » de la compétitivité : Rinehart,\n    James. The ideology of competitiveness. *Monthly Review*, 1995,\n    vol. 47 n° 5, p. 14.\n")
