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
    self.assertEqual(response.data['title'], 'Test pdf')
    self.assertEqual(response.data['url'], 'http://ec.europa.eu/health/files/eudralex/vol-1/reg_2016_161/reg_2016_161_en.pdf')

    # save as story caption
    url = reverse('caption-list')
    response = self.client.post(url, {
      'document': {
        'slug': 'test-pdf-2',
      },
      'story': story_id
    }, format='json')
    print response.data
    #self.assertEqual(response.data['slug'], 'test-pdf')


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
    