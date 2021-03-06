import os
from django.conf import settings
from django.core import mail
from django.test import TestCase
from django.test.client import Client
from django.test.runner import DiscoverRunner
from miller.models import Story, Comment, Author, Review
from django.contrib.auth.models import AnonymousUser, User, Group

class NoDbTestRunner(DiscoverRunner):
  """ A test runner to test without database creation/deletion """

  def setup_databases(self, **kwargs):
   pass

  def teardown_databases(self, old_config, **kwargs):
   pass


class ApiMillerTestCase(TestCase):
  fixtures = ('auth.group.json', )
  """
  This contain a common workflow for miller.
  We create a story with two authors and we set the clients for the different users/roles
  """
  def setUp(self):
    # create normal users
    self.user_A           = User.objects.create_user(
      username='douglas.adams', email='douglas@adams', password='top_secret')
    self.user_B           = User.objects.create_user(
      username='alessandro.baricco',  email='alessandro@baricco', password='top_secret', first_name='Alessandro', last_name='Baricco')
    self.user_C           = User.objects.create_user(
      username='lewis.carrol',  email='lewis@carrol', password='top_secret')
    self.user_D           = User.objects.create_user(
      username='gilles.deleuze',  email='gilles@deleuze', password='top_secret', first_name='Gilles', last_name='Deleuze')
    
    # group chief reviewer should have been created with fixtures
    self.group_chief_reviewer, created = Group.objects.get_or_create(name=Review.GROUP_CHIEF_REVIEWERS)
    self.assertEqual(created, False)
    self.group_chief_reviewer.user_set.add(self.user_D)

    # staff user
    self.user_staff       = User.objects.create_user(
      username='staff.user', email='staff@staff', password='top_secret', is_staff=True)

    self.users = [self.user_A, self.user_B, self.user_C, self.user_D, self.user_staff]
    # clients for normal users
    self.client_user_A    = Client(enforce_csrf_checks=False)
    self.client_user_B    = Client(enforce_csrf_checks=False)
    self.client_user_C    = Client(enforce_csrf_checks=False)
    
    # client for chief reviewers, yes it is a normal user with super powers but not enough
    self.client_user_D    = Client(enforce_csrf_checks=False)

    # client without authentification
    self.client_anonymous = Client(enforce_csrf_checks=False)
    
    # client for staff
    self.client_staff     = Client(enforce_csrf_checks=False)


    # force login for normal users
    self.client_user_A.force_login(user=self.user_A)
    self.client_user_B.force_login(user=self.user_B)
    self.client_user_C.force_login(user=self.user_C)
    self.client_user_D.force_login(user=self.user_D)

    # force login for staff user
    self.client_staff.force_login(user=self.user_staff)


    # create a story and add ownership
    self.story_A = Story.objects.create(
      title=u'The happy story of the Promo', 
      abstract=u'Considering the changes in the new brand buzz, the happy story has an happy ending',
      contents=u'## Basic \n\nWith a nice paragraph[^1] and some footnotes.\n\n### this is a third level\n\nsome text...\n\n[^1]: footnote content',
      owner=self.user_A
    )

    # check mail!!
    self.assertEqual(len(mail.outbox), 1)
    self.assertEqual(mail.outbox[0].to, [settings.DEFAULT_FROM_EMAIL])

    # check authorship
    self.story_A.create_first_author()
    self.assertEqual(self.story_A.authors.count(), 1)
    # Empty the test outbox
    mail.outbox = []

    # add authors
    self.author_A = self.user_A.authorship.first()
    self.author_C = self.user_C.authorship.first()

    self.story_A.authors.add(self.author_C)
    self.story_A.refresh_from_db()

    # check authors / expected: [douglas.adams, lewis.carrol]
    self.assertEqual(', '.join(self.story_A.authors.values_list('user__username', flat=True)), ', '.join([self.user_A.username, self.user_C.username]))
    
    self.assertEqual(self.story_A.owner.username, self.user_A.username)
    self.assertEqual(self.user_staff.is_staff, True)


  def cleanUp(self):
    path = self.story_A.get_path()
    self.story_A.delete()
    self.assertFalse(os.path.exists(path))

    for u in self.users:
      path = u.profile.get_path()
      u.delete()
      self.assertFalse(os.path.exists(path))