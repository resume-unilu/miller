#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json, codecs, markdown, os
from django.conf import settings
from django.shortcuts import render_to_response

# return a shared object to be sent to normal views
def _share(request):
  if request.user.is_authenticated():
    return {
      'user': json.dumps({
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
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

# static pages, from markdown contents
def pages(request, page):
  print page
  
  input_file = codecs.open(os.path.join(settings.PAGES_ROOT, "%s.md" % page), mode="r", encoding="utf-8")
  text = input_file.read()
  
  content = _share(request)
  content['contents'] = markdown.markdown(text)


  return render_to_response("page.html", content)