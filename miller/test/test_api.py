#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, json

from rest_framework.reverse import reverse
from django.contrib.auth.models import AnonymousUser, User

from miller.models import Story

from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

dir_path = os.path.dirname(os.path.realpath(__file__))

# python manage.py test miller.test.test_api.StoryTest
class StoryTest(APITestCase):
  def setUp(self):
    # Every test needs access to the request factory.
    self.factory = APIRequestFactory(enforce_csrf_checks=True)
    self.user = User.objects.create_user(
    username='jacob', email='jacob@jacob', password='top_secret')

    self.client.login(username='jacob', password='top_secret')

    

  def _empty_test_list(self):
    url = reverse('story-list')
    response = self.client.get(url, format='json')
    self.assertEqual(response.data, {"count":0,"next":None,"previous":None,"results":[]})


  def _test_create(self):
    url = reverse('story-list')
    response = self.client.post(url, {'title':'This is a sad old story'}, format='multipart')
    self.assertEqual(response.status_code, 201)
    self.assertEqual(response.data['slug'], 'this-is-a-sad-old-story')

    # throw an error, without any files!
    response = self.client.post(url, format='json')    
    self.assertEqual(response.status_code, 400)
    
    # should create a doc with the right content.
    with open(os.path.join(dir_path, 'test.docx'),'r') as docx:
      # The user should be the owner as well.
      response = self.client.post(url, {'source': docx, 'title':'This is a sad old story'}, format='multipart')
      self.assertEqual(response.data['slug'], 'this-is-a-sad-old-story-1')
    
    # test get from slug
    url = reverse('story-detail', args=[response.data['slug']])
    response = self.client.get(url, format='json')
    story_id = response.data['id']
    self.assertEqual(response.data['contents'], u'## La comp\xe9titivit\xe9 europ\xe9enne\xa0:\\\ncomp\xe9tition, coop\xe9ration, solidarit\xe9\n\nVersion\xa0: 30 mai 2016\n\n### 1\xa0L\u2019exigence d\u2019un engagement total\n\nLa comp\xe9titivit\xe9 est une obsession[^1].\n\n[^1]: Krugman, Paul. Competitiveness\xa0: A Dangerous Obsession. *Foreign\n    Affairs*, mars-avril 1994, vol.\xa073, n\xb02, pp.\xa028-44\xa0; pour une\n    critique similaire du \xab\xa0diktat\xa0\xbb de la comp\xe9titivit\xe9\xa0: Rinehart,\n    James. The ideology of competitiveness. *Monthly Review*, 1995,\n    vol.\xa047 n\xb0\xa05, p.\xa014.\n')


    # now the story are at least 2  
    url = reverse('story-list')
    response = self.client.get(url, format='json')
    self.assertEqual(response.data['count'], 2)

    # what if I change the contents of docx?
    url = reverse('story-detail', args=[story_id])
    response = self.client.patch(url, {'contents': 'oh good'}, format='multipart')
    self.assertEqual(response.data['contents'], 'oh good')
    
    # create a document and attach to the story. Only required fields.
    url = reverse('document-list')
    response = self.client.post(url, {
      'title': 'Test pdf',
      'type': 'rich',
      'metadata': ''
    }, format='multipart')
    self.assertEqual(response.data['slug'], 'test-pdf')

    # ups I did it again ???
    response = self.client.post(url, {
      'title': 'Test pdf',
      'type': 'rich',
      'metadata': ''
    }, format='multipart')
    # increase slug it's that sad.
    self.assertEqual(response.data['slug'], 'test-pdf-1')

    # now with a nice url.
    response = self.client.post(url, {
      'title': 'Test pdf',
      'type': 'rich',
      'metadata': '',
      'url': 'http://ec.europa.eu/health/files/eudralex/vol-1/reg_2016_161/reg_2016_161_en.pdf'
    }, format='multipart')
    self.assertEqual(response.data['slug'], 'test-pdf-2')
    self.assertEqual(response.data['url'], 'http://ec.europa.eu/health/files/eudralex/vol-1/reg_2016_161/reg_2016_161_en.pdf')


    # now with a nice url. It'st the same as before! Do not update.
    response = self.client.post(url, {
      'title': 'Test pdf duplicated',
      'type': 'rich',
      'metadata': '',
      'url': 'http://ec.europa.eu/health/files/eudralex/vol-1/reg_2016_161/reg_2016_161_en.pdf'
    }, format='multipart')
    
    self.assertEqual(response.data['slug'], 'test-pdf-2')
    self.assertEqual(response.data['title'], 'Test pdf duplicated')
    self.assertEqual(response.data['url'], 'http://ec.europa.eu/health/files/eudralex/vol-1/reg_2016_161/reg_2016_161_en.pdf')

    # save as story caption
    url = reverse('caption-list')
    response = self.client.post(url, {
      'document': {
        'slug': 'test-pdf-2',
      },
      'story': story_id
    }, format='json')
    # print response.data
    self.assertEqual(response.data['slug'], 'test-pdf-2') # return the document just attached.

    # save with youtube videos
    url = reverse('document-list')
    response = self.client.post(url, {
      'title': 'Test video youtube',
      'type': 'video',
      'metadata': '{"provider_url":"https://www.youtube.com/","description":"► Subscribe to the Financial Times on YouTube: http://bit.ly/FTimeSubs Jean-Claude Juncker, president of the European Commission, has provided details of the commission\'s plans to kickstart investment spending in Europe and seed growth. The FT\'s Ferdinando Giugliano provides a rundown of the scheme.","title":"Juncker\'s plan for Europe in 90 seconds | FT World","url":"http://www.youtube.com/watch?v=_gVDiBukGTE","author_name":"Financial Times","height":480,"thumbnail_width":480,"width":854,"html":"<iframe class=\\"embedly-embed\\" src=\\"//cdn.embedly.com/widgets/media.html?src=https%3A%2F%2Fwww.youtube.com%2Fembed%2F_gVDiBukGTE%3Ffeature%3Doembed&url=http%3A%2F%2Fw….jpg&key=28775d6020a142f1a3b7f24b77169194&type=text%2Fhtml&schema=youtube\\" width=\\"854\\" height=\\"480\\" scrolling=\\"no\\" frameborder=\\"0\\" allowfullscreen></iframe>","author_url":"https://www.youtube.com/user/FinancialTimesVideos","version":"1.0","provider_name":"YouTube","thumbnail_url":"https://i.ytimg.com/vi/_gVDiBukGTE/hqdefault.jpg","type":"video","thumbnail_height":360}',

      'url': 'https://www.youtube.com/watch?v=_gVDiBukGTE'
    }, format='multipart')

    self.assertEqual(response.data['metadata']['title'], "Juncker's plan for Europe in 90 seconds | FT World")
    #self.assertEqual(, 'test-video-youtube')
    self.assertEqual(response.data['slug'], 'test-video-youtube')
    
    # save with youtube videos, again.
    response = self.client.post(url, {
      'title': 'Test video youtube again',
      'type': 'video',
      'metadata': '{"provider_url":"https://www.youtube.com/","description":"► Subscribe to the Financial Times on YouTube: http://bit.ly/FTimeSubs Jean-Claude Juncker, president of the European Commission, has provided details of the commission\'s plans to kickstart investment spending in Europe and seed growth. The FT\'s Ferdinando Giugliano provides a rundown of the scheme.","title":"Juncker\'s plan for Europe in 90 seconds | FT World","url":"http://www.youtube.com/watch?v=_gVDiBukGTE","author_name":"Financial Times","height":480,"thumbnail_width":480,"width":854,"html":"<iframe class=\\"embedly-embed\\" src=\\"//cdn.embedly.com/widgets/media.html?src=https%3A%2F%2Fwww.youtube.com%2Fembed%2F_gVDiBukGTE%3Ffeature%3Doembed&url=http%3A%2F%2Fw….jpg&key=28775d6020a142f1a3b7f24b77169194&type=text%2Fhtml&schema=youtube\\" width=\\"854\\" height=\\"480\\" scrolling=\\"no\\" frameborder=\\"0\\" allowfullscreen></iframe>","author_url":"https://www.youtube.com/user/FinancialTimesVideos","version":"1.0","provider_name":"YouTube","thumbnail_url":"https://i.ytimg.com/vi/_gVDiBukGTE/hqdefault.jpg","type":"video","thumbnail_height":360}',

      'url': 'https://www.youtube.com/watch?v=_gVDiBukGTE'
    }, format='multipart')
    # print response.data['slug'], response.data
    self.assertEqual(response.data['title'], 'Test video youtube again') # do we update this...?
    self.assertEqual(response.data['slug'], 'test-video-youtube')

  def _test_delete_story(self):
    # delete every story
    Story.objects.all().delete()


  def _test_delete_user(self):
    path = self.user.profile.get_path()
    self.assertTrue(os.path.exists(path))
    self.user.delete()
    self.assertFalse(os.path.exists(path))

  def test_series(self):
    self._empty_test_list()
    self._test_create()
    self._test_delete_story()
    self._test_delete_user()
    