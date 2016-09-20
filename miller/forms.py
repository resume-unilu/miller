#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django import forms

class LoginForm(forms.Form):
  username = forms.CharField(max_length=128, widget=forms.TextInput)
  password = forms.CharField(max_length=64, label='Password', widget=forms.PasswordInput(render_value=False))

class SearchQueryForm(forms.Form):
  q = forms.CharField(max_length=128, widget=forms.TextInput)


class UploadDocxForm(forms.Form):
  docx = forms.FileField()