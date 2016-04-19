#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json, codecs, markdown, os

from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.utils.translation import ugettext as _

from miller.forms import LoginForm


# return a shared object to be sent to normal views
def _share(request, extra={}):
  d = {
    'title': settings.MILLER_TITLE
  }

  # if request.user.is_authenticated():
  #   d.update({
  #     'user': json.dumps({
  #       'first_name': request.user.first_name,
  #       'last_name': request.user.last_name,
  #       'short_url': request.user.profile.short_url,
  #       'username': request.user.username
  #     })
  #   })
  # else:
  #   d.update({
  #     'user': json.dumps({
  #       'short_url': 'anonymous' ,
  #       'username': 'anonymous'
  #     })
  #   })
  d.update(extra)
  return RequestContext(request, d)

# views here
def home(request):
  return render_to_response("index.html", _share(request))


def login_view(request):
  print 'login'
  if request.user.is_authenticated():
    return redirect('home')

  form = LoginForm(request.POST)
  next = request.GET.get('next', 'home')

  login_message = {
    'next': next if len( next ) else 'home'
  }

  if request.method != 'POST':
    return render_to_response('login.html', _share(request, extra=login_message))

  if not request.POST.get('remember_me', None):
    request.session.set_expiry(0)

  if form.is_valid():
    user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
    if user is not None:
      if user.is_active:
        login(request, user)
        # @todo: Redirect to next page

        return redirect(login_message['next'])
      else:
        login_message['error'] = _("user has been disabled")
    else:
      login_message['error'] = _("invalid credentials")
      # Return a 'disabled account' error message
  else:
    login_message['error'] = _("invalid credentials")
    login_message['invalid_fields'] = form.errors
  
  return render_to_response('login.html', _share(request, extra=login_message))

def logout_view( request ):
  logout(request)
  return redirect('home')

# static pages, from markdown contents
def pages(request, page):
  print page
  
  input_file = codecs.open(os.path.join(settings.PAGES_ROOT, "%s.md" % page), mode="r", encoding="utf-8")
  text = input_file.read()
  
  content = _share(request)
  content['contents'] = markdown.markdown(text)


  return render_to_response("page.html", content)