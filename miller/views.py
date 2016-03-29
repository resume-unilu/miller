#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.template import RequestContext

# views here
def home(request):
  return render_to_response("index.html", RequestContext(request, {}))