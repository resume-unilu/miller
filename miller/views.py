#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json, codecs, os, logging, datetime

from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.core import signing
from django.shortcuts import render_to_response, redirect, render
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.cache import cache_page

from templated_email import get_templated_mail, send_templated_mail

from miller.forms import LoginForm, SignupForm
from miller.models import Author, Story


logger = logging.getLogger('miller')


# return a shared object to be sent to normal views
def _share(request=None, extra={}):
  d = {
    'title': settings.MILLER_TITLE,
    'description': settings.MILLER_DESCRIPTION,
    'debug': settings.MILLER_DEBUG,
    'settings': json.dumps(settings.MILLER_SETTINGS),
    'oembeds': json.dumps(settings.MILLER_OEMBEDS)
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
  return d

# views here
@ensure_csrf_cookie
def home(request):
  return render(request, "index.html", _share(request))

# @cache_page(60 * 15)
@csrf_protect
def login_view(request):
  print 'login'
  if request.user.is_authenticated():
    print 'is authenticated...'
    return redirect('home')

  form = LoginForm(request.POST)
  next = request.GET.get('next', 'home')

  login_message = {
    'next': next if len( next ) else 'home'
  }

  if request.method != 'POST':
    return render(request, "login.html", _share(request, extra=login_message))

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
  
  return render(request, 'login.html', _share(request, extra=login_message))


@csrf_protect
def activation_complete(request):
  form = LoginForm
  return render(request, 'registration/activation_complete.html',  _share(request, extra={
    'form': form
  }))


@csrf_protect
def signup_view(request):
  if request.method == 'GET':
    signup_message = {}
    form = SignupForm(initial={
      'date_joined': datetime.datetime
    })
    next = request.GET.get('next', 'home')
  elif request.method == 'POST':
    #print 'ooooo', datetime.datetime
    # send registration email
    form = SignupForm(request.POST, initial={
      'date_joined': datetime.datetime
    })
    # confirm
    # register user and all


    if form.is_valid():
      logger.info('registration started  {first_name:%s}' % form.cleaned_data['first_name'])
      REGISTRATION_SALT = getattr(settings, 'REGISTRATION_SALT', 'registration')

      user = form.save(commit=False)
      # this is useful for auto saving the user related author cfr. miller.models.Author
      # we use here some code from https://github.com/ubernostrum/django-registration/blob/2.2/registration/backends/hmac/views.py
      user.first_name = form.cleaned_data['first_name']
      user.last_name  = form.cleaned_data['last_name']
      user.is_active = False

      user.save()
      logger.info('user saved  {pk:%s}' % user.pk)

      aut = Author.objects.filter(user=user).first()
      aut.affiliation = form.cleaned_data['affiliation']
      aut.save()
      
      logger.info('user-author saved  {author:%s, user.pk:%s}' % (aut, aut.user.pk))

      logger.info('registration success {pk:%s}' % user.pk)
      
      activation_key = signing.dumps(
        obj=user.username,
        salt=REGISTRATION_SALT
      )

      # send here the email with html
      # print activation_key
      # print settings.EMAIL_ACTIVATION_ACCOUNT
      # print user.email
      if hasattr(settings,'DISABLE_EMAIL_ACTIVATION'):
        print activation_key
      else:
        logger.info('sending activation email {pk:%s}' % user.pk)
        tmp = send_templated_mail(
          template_name='welcome.en_US', 
          from_email=settings.EMAIL_ACTIVATION_ACCOUNT,
          recipient_list=[user.email],
          context={
            'activation_link': request.build_absolute_uri(reverse('registration_activate', args=[activation_key])),
            'username': user.username,
            'fullname': aut.fullname,
            'site_name': settings.MILLER_TITLE,
            'site_url': request.build_absolute_uri(reverse('home'))
          }, 
          create_link=True
        )
      return redirect('home')


  return render(request, 'registration/registration_form.html', {
    'form': form
  })

  


def logout_view( request ):
  logout(request)
  return redirect('home')


# static pages, from markdown contents
def accessibility_page(request, page):
  input_file = codecs.open(os.path.join(settings.PAGES_ROOT, "%s.md" % page), mode="r", encoding="utf-8")
  text = input_file.read()
  
  content = _share(request)
  content['contents'] = text
  return render(request, "accessibility/page.html", content)


def accessibility_index(request):
  """
  load latest stuff, index page.
  """
  content = _share(request)

  highlights = Story.objects.filter(status=Story.PUBLIC, tags__slug= 'highlights').order_by('-date')[:10]
  top        = Story.objects.filter(status=Story.PUBLIC, tags__slug= 'top').order_by('-date')[:5]
  news       = Story.objects.filter(status=Story.PUBLIC, tags__slug= 'news').order_by('-date')[:10]

  

  content['top']        = top
  content['highlights'] = highlights
  content['news']       = news

  return render(request, "accessibility/index.html", content)


# accessible story
def accessibility_story(request, pk):
  from django.shortcuts import get_object_or_404
  """ single story page """
  if request.user.is_staff:
    q = Story.objects.all()
  elif request.user.is_authenticated():
    q = Story.objects.filter(Q(owner=request.user) | Q(status=Story.PUBLIC) | Q(authors__user=request.user)).distinct()
  else:
    q = Story.objects.filter(status=Story.PUBLIC)

  if pk.isdigit():
    story = get_object_or_404(q, pk=pk)
  else:
    story = get_object_or_404(q, slug=pk)

  content = _share(request)
  content['story'] = story
  return render(request, "accessibility/story.html", content)


def accessibility_stories(request, tag=None):
  content = _share(request)

  stories = Story.objects.filter(status=Story.PUBLIC, tags__category='writing')
  if tag is not None:
    stories = stories.filter(tags__slug=tag)

  content['stories'] = stories.distinct()
  return render(request, "accessibility/stories.html", content)


def accessibility_author(request, author):
  content = _share(request)

  author  = get_object_or_404(Author, slug=author)
  #stories = 
  return render(request, "accessibility/stories.html", content)


