#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, logging, json

from actstream import action

from miller import helpers

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models.signals import pre_delete, post_save
from django.dispatch import receiver
from django.contrib.auth.models import User



logger = logging.getLogger('miller')

class Review(models.Model):
  """
  Due by
  """
  EDITING      = 'editing'
  BLIND        = 'blind'
  DOUBLE_BLIND = 'double'

  CATEGORY_CHOICES = (
    (EDITING,      'editing'),
    (BLIND,        'blind'), # show story's author
    (DOUBLE_BLIND, 'double blind')
  )

  INITIAL   = 'initial'
  DRAFT     = 'draft'
  PRIVATE   = 'private'
  PUBLIC    = 'public'

  STATUS_CHOICES = (
    (INITIAL,   'initial'),
    (DRAFT,     'draft'),
    (PRIVATE,   'private'),
    (PUBLIC,    'public')
  )

  story    = models.ForeignKey('miller.Story', related_name='reviews')
  assignee = models.ForeignKey('auth.User'); # at least the first author, the one who owns the file.
  
  category = models.CharField(max_length=8, choices=CATEGORY_CHOICES, default=EDITING) # e.g. 'actor' or 'institution'
  
  status = models.CharField(max_length=8, choices=STATUS_CHOICES, default=INITIAL)

  due_date           = models.DateTimeField(null=True, blank=True)
  date_created       = models.DateTimeField(auto_now_add=True)
  date_last_modified = models.DateTimeField(auto_now=True)

  contents = models.TextField(default=json.dumps({
    'title': '',
    'content': ''
  }, indent=1),blank=True) # generic contents for the generic introduction? Is it ok?
  
  # List of fields
  FIELDS = ('thematic','thematic_score','interest', 'interest_score', 'originality', 'originality_score', 'innovation', 'innovation_score', 'interdiciplinarity', 'interdiciplinarity_score', 'methodology_score', 'methodology', 'clarity', 'clarity_score', 'argumentation_score', 'argumentation',
      'structure_score','structure', 'references', 'references_score', 'pertincence','pertincence_score',)

  thematic = models.TextField(null=True, blank=True)
  thematic_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(10),
      MinValueValidator(1)
    ]
  ) # Le tapuscrit se rattache-t-il aux thèmes abordés par le projet de recherche RESuME?
  interest = models.TextField(null=True, blank=True)
  interest_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(10),
      MinValueValidator(1)
    ]
  ) # Le tapuscrit présente-t-il un intérêt pour la communauté-cible du projet RESuME?
  originality = models.TextField(null=True, blank=True)
  originality_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(10),
      MinValueValidator(1)
    ]
  ) # Le sujet du tapuscrit se distingue-t-il par son innovation et son originalité?
  innovation = models.TextField(null=True, blank=True)
  innovation_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(10),
      MinValueValidator(1)
    ]
  ) # Le tapuscrit apporte-t-il des éléments d’interprétation ou de compréhension nouveaux du sujet abordé?
  interdiciplinarity = models.TextField(null=True, blank=True)
  interdiciplinarity_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(10),
      MinValueValidator(1)
    ]
  )# Le tapuscrit se distingue-t-il par son caractère interdisciplinaire?
  methodology = models.TextField(null=True, blank=True)
  methodology_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(10),
      MinValueValidator(1)
    ]
  )# La méthodologie appliquée par l’auteur est-elle appropriée et justifiée au regard du sujet traité?
  clarity = models.TextField(null=True, blank=True)
  clarity_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(10),
      MinValueValidator(1)
    ]
  ) # La problématique et les objectifs de recherche/d’analyse du tapuscrit sont-ils clairement exposés?
  argumentation = models.TextField(null=True, blank=True)
  argumentation_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(10),
      MinValueValidator(1)
    ]
  ) # L’argumentation développée dans le tapuscrit est-elle convaincante au regard de la problématique retenue?
  structure = models.TextField(null=True, blank=True)
  structure_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(10),
      MinValueValidator(1)
    ]
  )# La structure du tapuscrit, l’intitulé des différentes sections sont-ils signifiants?
  references = models.TextField(null=True, blank=True)
  references_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(10),
      MinValueValidator(1)
    ]
  )#Les références citées en notes de bas de page sont-elles justifiées, pertinentes, actualisées?
  pertincence = models.TextField(null=True, blank=True)
  pertincence_score = models.IntegerField(
    null=True,
    blank=True,
    validators=[
      MaxValueValidator(10),
      MinValueValidator(1)
    ]
  )# Les ressources documentaires sélectionnées contribuent-elles utilement à l’argumentation?

  def __unicode__(self):
    return '%s:%s - reviewer:%s' % (self.category, self.story.title, self.assignee.username)

  # send email on save
  # def 
