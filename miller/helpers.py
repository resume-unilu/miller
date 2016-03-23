#!/usr/bin/env python
# -*- coding: utf-8 -*-
import shortuuid

"""
Helpers.

usage sample:

  import miller.helpers

  print helpers.echo()

"""

def create_short_url(): 
  return shortuuid.uuid()[:7]