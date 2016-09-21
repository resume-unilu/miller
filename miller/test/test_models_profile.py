import os
from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from miller import helpers


dir_path = os.path.dirname(os.path.realpath(__file__))

class ProfileTest(TestCase):
  def setUp(self):
    # Every test needs access to the request factory.
    self.user = User.objects.create_user(
        username='test-user-profile', 
        email='jacob@jacob', 
        password='top_secret')

  def test_create(self):
    # check that the profile exist
    path = self.user.profile.get_path()
    self.assertTrue(os.path.exists(path))
    
    created, collection, zotero = helpers.get_or_create_zotero_collection(self.user.username)
    
    if collection:
        self.assertEqual(collection['data']['name'], self.user.username)
    # check that a 
    self.user.delete()
    self.assertFalse(os.path.exists(path))
    # check that the user has been deleted
    