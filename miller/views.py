#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json, codecs, os, logging, datetime

from django.conf import settings
from django.contrib.auth import login, logout, authenticate
from django.core import signing
from django.shortcuts import render_to_response, redirect, render, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.cache import cache_page

from templated_email import get_templated_mail, send_templated_mail

from miller.forms import LoginForm, SignupForm, ContactForm
from miller.models import Author, Story, Page


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

def _loadlocale():
    """
    Load locale from JSON file if any.
    """
    contents = {}
    if settings.MILLER_LOCALISATION_TABLE_AS_JSON is not None:
        contents = json.load(open(settings.MILLER_LOCALISATION_TABLE_AS_JSON))
    return contents

# views here
@ensure_csrf_cookie
def home(request):
  return render(request, "miller/index.html")
  #, _share(request))

def timelinejs(request, gsid):
  return render(request, "miller/timelinejs.iframe.html", {
    'gsid': gsid,
    'stylesheet_url': settings.MILLER_TIMELINEJS_STYLESHEET
  })

@csrf_protect
def activation_complete(request):
  form = LoginForm
  return render(request, 'registration/activation_complete.html',  _share(request, extra={
    'form': form
  }))

@csrf_protect
def contact_view(request):
  email_status = 'ready'
  language = request.POST.get('lang','en') if request.method == 'POST' else request.GET.get('lang','en')
  next = request.POST.get('next',None) if request.method == 'POST' else request.GET.get('next',None)

  # we don't check available languages. Default is good.
  if not language in settings.LANGUAGES_ISO_6391:
     language = 'en'
  # should be done in form... @todo
  if next:
     import re
     next = '{0}/{1}'.format(settings.MILLER_HOST, re.sub(r'^[^\/]*\/*', '', next));
  else:
     next = settings.MILLER_HOST

  if request.method == 'POST':
    form = ContactForm(request.POST, initial={
      'date_joined': datetime.datetime
    })
    if form.is_valid():
        #print 'contact_view IS VALID'
        context = {
            'site_name': settings.MILLER_TITLE
        }
        context.update(form.cleaned_data)
        
        try:
          tmp = send_templated_mail(
            template_name='contact_confirmation_for_staff.en',
            from_email=form.cleaned_data['email_from'],
            recipient_list=[settings.DEFAULT_FROM_EMAIL],
            context=context,
            fail_silenty=False,
            #create_link=True
          )
          # send recipient email
          tmp = send_templated_mail(
            template_name='contact_confirmation_for_recipient.{0}'.format(language),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[form.cleaned_data['email_from']],
            context=context,
            fail_silenty=False,
            #create_link=True
          )
        except Exception as e:
          logger.debug('sending contact email failed')
          logger.exception(e)
          email_status = 'exception'

        else:
          logger.info('sending contact email success')
          email_status = 'success'
          # return a different template with the go back button here
          return render(request, 'miller/contacts_complete.html', {
            'form': form,
            'next': next,
            'errors': {},
            'language': language,
            'locale': _loadlocale()
          })
  else:
    form = ContactForm(initial={
      'date_joined': datetime.datetime
    })

  return render(request, 'miller/contacts.html', {
    'form': form,
    'errors': {} if form.is_valid() else form.errors.as_json(),
    'next': next,
    'email_status': email_status,
    'language': language,
    'locale': _loadlocale()
  })


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
      logger.info('registration started  {username:%s}, form is valid' % form.cleaned_data['username'])
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



      activation_key = signing.dumps(
        obj=user.username,
        salt=REGISTRATION_SALT
      )

      # send here the email with html
      # print activation_key
      # print settings.EMAIL_ACTIVATION_ACCOUNT
      # print user.email
      try:
        tmp = send_templated_mail(
          template_name='welcome.en_US',
          from_email=settings.DEFAULT_FROM_EMAIL,
          recipient_list=[user.email],
          context={
            'activation_link': request.build_absolute_uri(reverse('registration_activate', args=[activation_key])),
            'username': user.username,
            'fullname': aut.fullname,
            'site_name': settings.MILLER_TITLE,
            'site_url': settings.MILLER_SETTINGS['host']
          },
          fail_silenty=False,
          #create_link=True
        )
        logger.info('activation email sent to user {pk:%s}' % user.pk)
      except Exception as e:
        logger.debug('sending activation email failed {pk:%s, key:%s}' % (user.pk, activation_key))

        logger.exception(e)
      else:
        logger.info('registration success {pk:%s}' % user.pk)
      return redirect('home')


  return render(request, 'registration/registration_form.html', {
    'form': form
  })


# accessible doi
def accessibility_doi(request, prefix, short_url, publication_year):
  story = get_object_or_404(Story.objects.filter(status=Story.PUBLIC), short_url=short_url)
  content = _share(request)
  content['story'] = story
  return render(request, "miller/accessibility/story.html", content)


def logout_view( request ):
  logout(request)
  return redirect('home')


# static pages, from markdown contents
def accessibility_page(request, page):
  page = get_object_or_404(Page, slug=page)
  #input_file = codecs.open(os.path.join(settings.PAGES_ROOT, "%s.md" % page), mode="r", encoding="utf-8")
  #text = input_file.read()

  content = _share(request)
  content['contents'] = page.contents
  return render(request, "miller/accessibility/page.html", content)


def accessibility_index(request):
  """
  load latest stuff, index page.
  """
  content = _share(request)

  highlights = Story.objects.filter(status=Story.PUBLIC, tags__slug='highlights').order_by('-date')[:10]
  top        = Story.objects.filter(status=Story.PUBLIC, tags__slug='top').order_by('-date')[:5]
  news       = Story.objects.filter(status=Story.PUBLIC, tags__slug='news').order_by('-date')[:10]


  content['top']        = top
  content['highlights'] = highlights
  content['news']       = news

  return render(request, "miller/accessibility/index.html", content)


# accessible story
def accessibility_story(request, pk):

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
  return render(request, "miller/accessibility/story.html", content)


def accessibility_collection(request, pk):
  """ single story page """
  if request.user.is_staff:
    q = Story.objects.all()
  elif request.user.is_authenticated():
    q = Story.objects.filter(Q(owner=request.user) | Q(status=Story.PUBLIC) | Q(authors__user=request.user)).distinct()
  else:
    q = Story.objects.filter(status=Story.PUBLIC)

  q = q.filter(tags__slug='collection')

  if pk.isdigit():
    story = get_object_or_404(q, pk=pk)
  else:
    story = get_object_or_404(q, slug=pk)

  content = _share(request)
  content['story'] = story
  return render(request, "miller/accessibility/collection.html", content)



def accessibility_stories(request, tag=None):
  content = _share(request)

  stories = Story.objects.filter(status=Story.PUBLIC, tags__category='writing')
  if tag is not None:
    stories = stories.filter(tags__slug=tag)

  content['stories'] = stories.distinct()
  return render(request, "miller/accessibility/stories.html", content)


def accessibility_author(request, author, tag=None):
  content = _share(request)

  author  = get_object_or_404(Author, slug=author)

  stories = Story.objects.filter(authors=author, status=Story.PUBLIC).distinct()

  if tag:
    stories = stories.filter(tags__slug=tag).distinct()

  content['author'] = author;
  content['stories'] = stories;
  #stories =
  return render(request, "miller/accessibility/stories.html", content)
