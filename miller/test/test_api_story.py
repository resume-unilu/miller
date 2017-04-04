#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json,os
from actstream.models import any_stream
    
from django.core import mail
from django.test import TestCase
from rest_framework.reverse import reverse

from miller.test import ApiMillerTestCase
from miller.models import Comment, Story

dir_path = os.path.dirname(os.path.realpath(__file__))


# python manage.py test miller.test.test_api_story.StoryTest
class StoryTest(ApiMillerTestCase):

  def _test_story_list(self):
    response = self.client_user_A.get('/api/story/%s/' % self.story_A.slug)
    self.assertEqual(response.json()['title'], self.story_A.title)

    response = self.client_user_A.get('/api/story/')
    self.assertEqual(response.status_code, 200)
    self.assertEqual(response.json()['count'] > 0, True)

  def _test_create_from_docx(self):
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
  
  def _test_story_publish(self):
    # user B asks for story publish. Nope!
    response = self.client_user_B.post('/api/story/%s/publish/' % self.story_A.slug)
    self.assertEqual(response.status_code, 404)

    # user A asks for story publish. Of course, it is the owner
    response = self.client_user_A.post('/api/story/%s/publish/' % self.story_A.slug)
    self.assertEqual(response.status_code, 200)

    self.story_A.refresh_from_db()
    self.assertEqual(self.story_A.status, Story.PENDING)

    # story has 2 authors with emails.
    self.assertEqual(len(mail.outbox), 3)
    
    # first thing, the submitter username
    self.assertEqual(mail.outbox[0].subject.split(' ')[0], self.user_A.username)
    mail.outbox = []


  def _test_attach_documents(self):
    # create a document and attach to the story. Only required fields.
    url_document_list = reverse('document-list')

    # anonymous users cannot attach documents.
    response = self.client_anonymous.post(url_document_list, {
      'title': 'Test pdf',
      'type': 'rich',
      'metadata': ''
    }, format='multipart')
    self.assertEqual(response.status_code, 403)


    response = self.client_user_A.post(url_document_list, {
      'title': 'Test pdf',
      'type': 'rich',
      'metadata': ''
    }, format='multipart')
    self.assertEqual(response.status_code, 201)
    self.assertEqual(response.json()['slug'], 'test-pdf')

    # ups I did it again ???
    response = self.client_user_B.post(url_document_list, {
      'title': 'Test pdf',
      'type': 'rich',
      'metadata': ''
    }, format='multipart')
    # increase slug it's that sad.
    self.assertEqual(response.status_code, 201)
    self.assertEqual(response.data['slug'], 'test-pdf-1')

    # now with a nice url.
    response = self.client_user_A.post(url_document_list, {
      'title': 'Test pdf',
      'type': 'rich',
      'metadata': '',
      'url': 'http://ec.europa.eu/health/files/eudralex/vol-1/reg_2016_161/reg_2016_161_en.pdf'
    }, format='multipart')
    response_json = json.loads(response.content)
    self.assertEqual(response_json['slug'], 'test-pdf-2')
    self.assertEqual(response_json['url'], 'http://ec.europa.eu/health/files/eudralex/vol-1/reg_2016_161/reg_2016_161_en.pdf')


    # now with a nice url. It'st the same as before! The document is not locked, though.
    response = self.client_user_A.post(url_document_list, {
      'title': 'Test pdf duplicated',
      'type': 'rich',
      'metadata': '',
      'url': 'http://ec.europa.eu/health/files/eudralex/vol-1/reg_2016_161/reg_2016_161_en.pdf'
    }, format='multipart')
    response_json = json.loads(response.content)
    self.assertEqual(response_json['slug'], 'test-pdf-2')
    self.assertEqual(response_json['title'], 'Test pdf')
    self.assertEqual(response_json['url'], 'http://ec.europa.eu/health/files/eudralex/vol-1/reg_2016_161/reg_2016_161_en.pdf')

    # save as story caption
    # response = self.client_user_A.post(reverse('caption-list'), {
    #   'document': {
    #     'slug': 'test-pdf-2',
    #   },
    #   'story': self.story_A.id
    # }, format='json')
    # # print response.data
    # self.assertEqual(response.status_code, 201)
    # self.assertEqual(response.json()['slug'], 'test-pdf-2') # return the document just attached.

    # save a youtube video
    response = self.client_user_A.post(url_document_list, {
      'title': 'Test video youtube',
      'type': 'video',
      'metadata': '{"provider_url":"https://www.youtube.com/","description":"► Subscribe to the Financial Times on YouTube: http://bit.ly/FTimeSubs Jean-Claude Juncker, president of the European Commission, has provided details of the commission\'s plans to kickstart investment spending in Europe and seed growth. The FT\'s Ferdinando Giugliano provides a rundown of the scheme.","title":"Juncker\'s plan for Europe in 90 seconds | FT World","url":"http://www.youtube.com/watch?v=_gVDiBukGTE","author_name":"Financial Times","height":480,"thumbnail_width":480,"width":854,"html":"<iframe class=\\"embedly-embed\\" src=\\"//cdn.embedly.com/widgets/media.html?src=https%3A%2F%2Fwww.youtube.com%2Fembed%2F_gVDiBukGTE%3Ffeature%3Doembed&url=http%3A%2F%2Fw….jpg&key=28775d6020a142f1a3b7f24b77169194&type=text%2Fhtml&schema=youtube\\" width=\\"854\\" height=\\"480\\" scrolling=\\"no\\" frameborder=\\"0\\" allowfullscreen></iframe>","author_url":"https://www.youtube.com/user/FinancialTimesVideos","version":"1.0","provider_name":"YouTube","thumbnail_url":"https://i.ytimg.com/vi/_gVDiBukGTE/hqdefault.jpg","type":"video","thumbnail_height":360}',

      'url': 'https://www.youtube.com/watch?v=_gVDiBukGTE'
    }, format='multipart')
    response_json = json.loads(response.content)
    self.assertEqual(response_json['metadata']['title'], "Juncker's plan for Europe in 90 seconds | FT World")
    #self.assertEqual(, 'test-video-youtube')
    self.assertEqual(response_json['slug'], 'test-video-youtube')
    
    # save with youtube videos, again.
    response = self.client_user_B.post(url_document_list, {
      'title': 'Test video youtube again',
      'type': 'video',
      'metadata': '{"provider_url":"https://www.youtube.com/","description":"► Subscribe to the Financial Times on YouTube: http://bit.ly/FTimeSubs Jean-Claude Juncker, president of the European Commission, has provided details of the commission\'s plans to kickstart investment spending in Europe and seed growth. The FT\'s Ferdinando Giugliano provides a rundown of the scheme.","title":"Juncker\'s plan for Europe in 90 seconds | FT World","url":"http://www.youtube.com/watch?v=_gVDiBukGTE","author_name":"Financial Times","height":480,"thumbnail_width":480,"width":854,"html":"<iframe class=\\"embedly-embed\\" src=\\"//cdn.embedly.com/widgets/media.html?src=https%3A%2F%2Fwww.youtube.com%2Fembed%2F_gVDiBukGTE%3Ffeature%3Doembed&url=http%3A%2F%2Fw….jpg&key=28775d6020a142f1a3b7f24b77169194&type=text%2Fhtml&schema=youtube\\" width=\\"854\\" height=\\"480\\" scrolling=\\"no\\" frameborder=\\"0\\" allowfullscreen></iframe>","author_url":"https://www.youtube.com/user/FinancialTimesVideos","version":"1.0","provider_name":"YouTube","thumbnail_url":"https://i.ytimg.com/vi/_gVDiBukGTE/hqdefault.jpg","type":"video","thumbnail_height":360}',

      'url': 'https://www.youtube.com/watch?v=_gVDiBukGTE'
    }, format='multipart')
    response_json = json.loads(response.content)
    # print response_json['slug'], response_json
    self.assertEqual(response_json['title'], 'Test video youtube') # we do not update anything
    self.assertEqual(response_json['slug'], 'test-video-youtube')


  def test_suite(self):
    self._test_story_publish()
    self._test_story_list()
    self._test_create_from_docx()
    self._test_attach_documents()
    self.cleanUp()