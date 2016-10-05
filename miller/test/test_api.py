import os, json

from rest_framework.reverse import reverse
from django.contrib.auth.models import AnonymousUser, User
from rest_framework.test import APITestCase, APIRequestFactory, force_authenticate
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

dir_path = os.path.dirname(os.path.realpath(__file__))

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
    doc_id = response.data['id']
    self.assertEqual(response.data['contents'], u'## La comp\xe9titivit\xe9 europ\xe9enne\xa0:\\\ncomp\xe9tition, coop\xe9ration, solidarit\xe9\n\nVersion\xa0: 30 mai 2016\n\n### 1\xa0L\u2019exigence d\u2019un engagement total\n\nLa comp\xe9titivit\xe9 est une obsession[^1].\n\n[^1]: Krugman, Paul. Competitiveness\xa0: A Dangerous Obsession. *Foreign\n    Affairs*, mars-avril 1994, vol.\xa073, n\xb02, pp.\xa028-44\xa0; pour une\n    critique similaire du \xab\xa0diktat\xa0\xbb de la comp\xe9titivit\xe9\xa0: Rinehart,\n    James. The ideology of competitiveness. *Monthly Review*, 1995,\n    vol.\xa047 n\xb0\xa05, p.\xa014.\n')

    # now the story are at least 2  
    url = reverse('story-list')
    response = self.client.get(url, format='json')
    self.assertEqual(response.data['count'], 2)

    # what if I change the contents of docx?
    url = reverse('story-detail', args=[doc_id])
    response = self.client.patch(url, {'contents': 'oh good'}, format='multipart')
    self.assertEqual(response.data['contents'], 'oh good')
    

  def test_series(self):
    self._empty_test_list()
    self._test_create()
    