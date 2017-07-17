#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, json
from miller import helpers

dir_path = os.path.dirname(os.path.realpath(__file__))

#
#  test helpers module
#  python manage.py test miller.test.test_helpers.HelpersTest --testrunner=miller.test.NoDbTestRunner
#
from django.test import TestCase
from django.conf import settings

class HelpersTest(TestCase):
  """
  test + '_' + name of the function.
  """
  def test_get_values_from_dict(self):
    complex_dict = {
      'modules': [
        {
          'document': {
            'pk': 1982,
            'related':[
              {
                'pk': 1990,
              }
            ]
          }
        }
      ], 
      'overlay': {
        'background': {
          'pk': 30
        }
      }
    }

    pks = helpers.get_values_from_dict(complex_dict, key='pk')

    self.assertEquals('1982,1990,30', ','.join(str(x) for x in pks))
