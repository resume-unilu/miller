#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os,codecs

from django.db import models
from miller.models import Document, Story

class Caption(models.Model):
  document      = models.ForeignKey(Document, on_delete=models.CASCADE)
  story         = models.ForeignKey(Story, on_delete=models.CASCADE)
  date_created  = models.DateField(auto_now=True)
  
  contents      = models.TextField()

  class Meta:
    ordering = ["-date_created"]
    verbose_name_plural = "captions"