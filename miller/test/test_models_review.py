#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from django.contrib.auth.models import AnonymousUser, User
from django.conf import settings
from django.core import mail
from django.test import TestCase
from miller import helpers
from miller.models import Story, Profile, Review


dir_path = os.path.dirname(os.path.realpath(__file__))

class ReviewTest(TestCase):
  """
  Test review generation; report generation; md saving.
  
  cmd:
  ```
  python manage.py test miller.test.test_models_review.ReviewTest
  ```
  """

  def setUp(self):
    self.assignee = User.objects.create_user(
        username='malatesta', 
        email='jacob@jacob', 
        password='top_secret')

    self.assigned_by = User.objects.create_user(
        username='virgilio', 
        email='virgilio@manuamegenu.it', 
        password='calabrirepuere')

    self.dantealighieri = User.objects.create_user(
        username='dante-alighieri', 
        email='dantealighieri@divinacommedia.it', 
        password='BeAtRiCe')

    self.story = Story.objects.create(
        title ='CANTO I - inferno',
        abstract= u"Incomincia la Comedia di Dante Alleghieri di Fiorenza, ne la quale tratta de le pene e punimenti de' vizi e de' meriti e premi de le virtù. Comincia il canto primo de la prima parte la quale si chiama Inferno, nel qual l'auttore fa proemio a tutta l'opera.",
        contents=u"Nel mezzo del cammin di nostra vita\nmi ritrovai per una selva oscura,\nché la diritta via era smarrita.\n\nAhi quanto a dir qual era è cosa dura\nesta selva selvaggia e aspra e forte\nche nel pensier rinova la paura!\n[...]",
        owner=self.dantealighieri
    )

    # a mail should have been set, a new story has been created!!
    # Test that one message has been sent.
    self.assertEqual(len(mail.outbox), 1)

    # Verify that the subject of the first message is correct.
    self.assertEqual(mail.outbox[0].subject, u'A new publication has been created on %s' % settings.MILLER_TITLE)


  def assign_review(self):
    # check that the profile exist
    path = self.dantealighieri.profile.get_path()
    self.assertTrue(os.path.exists(path))
    
    review = Review.objects.create(story=self.story, assignee=self.assignee, assigned_by=self.assigned_by)
    # default: editing request.
    self.assertEqual(review.category, Review.EDITING)
    self.assertEqual(len(mail.outbox), 2)
    self.assertEqual(mail.outbox[1].subject, u'A new editing task has been assigned to you')

    review_dblind = Review.objects.create(story=self.story, assignee=self.assignee, assigned_by=self.assigned_by, category=Review.DOUBLE_BLIND)

    # autocalculate score oes not make sense now!
    self.assertEqual(review_dblind.score, None)

    # Test that one message has been sent.
    self.assertEqual(len(mail.outbox), 3)

    # # Verify that the subject of the first message is correct.
    # print mail.outbox[1].subject, mail.outbox[1]
    self.assertEqual(mail.outbox[2].subject, u'A new review has been assigned to you')
    # check that the user has been deleted
    # .. set review...
    review_dblind.status = Review.DRAFT
    review_dblind.structure_score = 4
    review_dblind.save()

    # Now score should have been calculated.
    self.assertEqual(review_dblind.score, 4)


  def remove_story(self):
    self.story.delete()

  def remove_users(self):
    path = self.dantealighieri.profile.get_path()
    self.dantealighieri.delete()
    self.assertFalse(os.path.exists(path))
    path = self.assigned_by.profile.get_path()
    self.assigned_by.delete()
    self.assertFalse(os.path.exists(path))
    path = self.assignee.profile.get_path()
    self.assignee.delete()
    self.assertFalse(os.path.exists(path))

  def test_suite(self):
    self.assign_review()
    self.remove_story()
    self.remove_users()