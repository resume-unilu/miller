#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from django.shortcuts import render_to_response

# return a shared object to be sent to normal views
def _share(request):
  if request.user.is_authenticated():
    return {
      'user': json.dumps({
        'short_url': request.user.profile.short_url,
        'username': request.user.username
      })
    }
  else:
    return {
      'user': json.dumps({
        'short_url': 'anonymous' ,
        'username': 'anonymous'
      })
    }

# views here
def home(request):
  return render_to_response("index.html", _share(request))