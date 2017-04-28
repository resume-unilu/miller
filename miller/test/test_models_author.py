#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from django.contrib.auth.models import AnonymousUser, User
from django.test import TestCase
from miller import helpers
from miller.models import Document, Author


dir_path = os.path.dirname(os.path.realpath(__file__))

# python manage.py test miller.test.test_models_author.AuthorTest
class AuthorTest(TestCase):

  def setUp(self):
    self.user = User.objects.create_user(
        username='jacob-generic', 
        first_name='Jacob',
        last_name='Generic',
        email='jacob@jacob', 
        password='top_secret')

    self.userB = User.objects.create_user(
        username='arturo-toscanini', 
        first_name='Arturo',
        last_name='Toscanini',
        email='arturo@toscanini', 
        password='top_secret')


  def test_creation(self):
    self.assertEqual(self.user.authorship.first().fullname, 'Jacob Generic')
    self.assertEqual(self.user.authorship.first().slug, 'jacob-generic')

    self.assertEqual(self.userB.authorship.first().fullname, 'Arturo Toscanini')
    
    # we get the right author
    aut = Author.objects.filter(user=self.userB).first()
    self.assertEqual(self.userB.authorship.first().fullname, aut.fullname)

    # we add another author for this user, omonimous
    autOm = Author(user=self.user, fullname='jacob generic')
    autOm.save()

    self.assertEqual(self.user.authorship.count(), 2)
    self.assertEqual(u','.join(sorted(self.user.authorship.values_list('slug', flat=True))), 'jacob-generic,jacob-generic-1')
    