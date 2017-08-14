#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
from django import forms
from django.conf import settings

from captcha.fields import CaptchaField
from django.contrib.auth.models import User
from registration.forms import RegistrationFormUniqueEmail



class ExtractCaptionFromStory(forms.Form):
  key    = forms.ChoiceField(choices=[('slug','slug'), ('pk','pk'), ('id','id')], required=True)
  parser = forms.ChoiceField(choices=[('json','json')], required=True)


class LoginForm(forms.Form):
  username = forms.CharField(max_length=128, widget=forms.TextInput)
  password = forms.CharField(max_length=64, label='Password', widget=forms.PasswordInput(render_value=False))

class SearchQueryForm(forms.Form):
  q = forms.CharField(max_length=128, widget=forms.TextInput, required=False)
  tags = forms.CharField(max_length=128, required=False)
  authors = forms.CharField(max_length=128, required=False)

class UploadDocxForm(forms.Form):
  docx = forms.FileField()

class CaptionForm(forms.Form):
  document = forms.RegexField(max_length=150, regex=r'^[a-zA-Z\-\_\.\d]+$', required=True)
  story    = forms.RegexField(max_length=150, regex=r'^[a-zA-Z\-\_\.\d]+$', required=True)

class SignupForm(RegistrationFormUniqueEmail):
  captcha     = CaptchaField()

  tos         = forms.BooleanField(widget=forms.CheckboxInput)

  first_name  = forms.CharField(min_length=3, max_length=128, widget=forms.TextInput)
  last_name   = forms.CharField(min_length=3, max_length=128, widget=forms.TextInput)
  affiliation = forms.CharField(required=False, max_length=500, widget=forms.TextInput)

class URLForm(forms.Form):
  url = forms.URLField()

class GitTagForm(forms.Form):
  tag = forms.RegexField(max_length=24, regex=r'^[a-zA-Z\-\_\.\d]+$', required=True)
  message = forms.CharField(max_length=128, required=False)


class DOICiteForm(forms.Form):
  LANGUAGE_CHOICES = tuple((re.sub(r'([a-z]{2})$', lambda x: x.group(1).upper(), lang[0]), lang[1]) for lang in settings.LANGUAGES)

  contentType = forms.ChoiceField(choices=settings.MILLER_DOI_RESOLVER_CONTENT_TYPES)
  style       = forms.ChoiceField(choices=settings.MILLER_DOI_RESOLVER_STYLES) 
  locale      = forms.ChoiceField(choices=LANGUAGE_CHOICES, required=False) 