#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAdminUser

from rest_framework import serializers,viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import  api_view, permission_classes, detail_route, list_route # cfr StoryViewSet

from miller.models import Story, Tag, Document, Caption, Comment
from miller.api.utils import Glue
from miller.api.fields import OptionalFileField, JsonField
from miller.api.serializers import LiteDocumentSerializer, MatchingStorySerializer, AuthorSerializer, TagSerializer, StorySerializer, LiteStorySerializer, CreateStorySerializer, CommentSerializer


# ViewSets define the view behavior. Filter by status
class StoryViewSet(viewsets.ModelViewSet):
  queryset = Story.objects.all()
  serializer_class = CreateStorySerializer

  def _getUserAuthorizations(self, request):
    if request.user.is_staff:
      q = Story.objects.all()
    elif request.user.is_authenticated:
      q = Story.objects.filter(Q(owner=request.user) | Q(status=Story.PUBLIC) | Q(authors__user=request.user)).distinct()
    else:
      q = Story.objects.filter(status=Story.PUBLIC).distinct()
    return q


  # retrieve by PK or slug
  def retrieve(self, request, *args, **kwargs):
    q = self._getUserAuthorizations(request)
    # if request.user.is_authenticated():
    #   q = Q(owner=request.user) | Q(status=Story.PUBLIC)
    # else:
    #   q = Q(status=Story.PUBLIC)

    if 'pk' in kwargs and not kwargs['pk'].isdigit():
      story = get_object_or_404(q, slug=kwargs['pk'])
    else:
      story = get_object_or_404(q, pk=kwargs['pk'])
    
    ckey = 'story.%s' % story.short_url
    #print 'nocache:', request.query_params.get('nocache', None)

    if not request.query_params.get('nocache', None) and cache.has_key(ckey):
      #print 'serve cahced', ckey
      return Response(cache.get(ckey))

    serializer = StorySerializer(story,
        context={'request': request},
    )
    #print 'set cache', ckey
    cache.set('story.%s' % story.short_url, serializer.data)
    
    return Response(serializer.data)
  

  def list(self, request):
    stories = self._getUserAuthorizations(request)
    g = Glue(request=request, queryset=stories)
    
    stories = g.queryset

    if 'status' not in g.filters:
      stories = stories.exclude(status=Story.DELETED)

    # add orderby
    # print stories.query
    page    = self.paginate_queryset(stories)
    
    if page is not None:
      serializer = LiteStorySerializer(page, many=True, context={'request': request})
      return self.get_paginated_response(serializer.data)

    serializer = LiteStorySerializer(page, many=True, context={'request': request})
    return Response(serializer.data)


  # for some tags require the request user to be staff user
  # @permission_classes((IsAdminUser, ))
  def partial_update(self, request, *args, **kwargs):
    # print request.user
    return super(StoryViewSet, self).partial_update(request, *args, **kwargs)


  @detail_route(methods=['get'])
  def download(self, request, pk):
    q = self._getUserAuthorizations(request)
    story = get_object_or_404(q, pk=pk)


    import os, mimetypes
    from wsgiref.util import FileWrapper
    from django.http import StreamingHttpResponse
    from django.utils.text import slugify

    attachment = story.download(outputFormat='pdf')
    mimetype = mimetypes.guess_type(attachment)[0]
    # print attachment,mimetype
    
    response = StreamingHttpResponse(FileWrapper( open(attachment), 8192), content_type=mimetype)
    response['Content-Length'] = os.path.getsize(attachment)  
    response['Content-Disposition'] = 'attachment; filename="%s.%s"' % (slugify(story.title),mimetypes.guess_extension(mimetype))
      
    return response

  
  @list_route(methods=['get'])
  def search(self, request):
    from miller.forms import SearchQueryForm
    from miller.helpers import search_whoosh_index
    form = SearchQueryForm(request.query_params)
    if not form.is_valid():
      return Response(form.errors, status=status.HTTP_400_BAD_REQUEST)
    # get the results
    filters = {
      'classname': u'story',
    }

    if form.cleaned_data['tags']:
      filters['tags'] = form.cleaned_data['tags']
    
    if form.cleaned_data['authors']:
      filters['authors'] = form.cleaned_data['authors']
    
    if not request.user.is_staff:
      filters['status'] = Story.PUBLIC

    results = search_whoosh_index(form.cleaned_data['q'], **filters)
    
    # check if the user is allowed this content
    # if request.user.is_authenticated():
    #   stories = self.queryset.filter(Q(owner=request.user) | Q(authors__in=request.user.authorship.all()) | Q(status=Story.PUBLIC)).filter(**filters).distinct()
    # else:
    stories = self.queryset.filter(short_url__in = [hit['short_url'] for hit in results]).distinct()


    def mapper(d):
      d.matches = []
      for hit in results:
        if d.short_url == hit['short_url']:
          d.matches = hit
          break
      return d
    # enrich stories items (max 10 items)
    stories = map(mapper, stories)
    page    = self.paginate_queryset(stories)

    serializer = MatchingStorySerializer(stories, many=True,
      context={'request': request}
    )
    return self.get_paginated_response(serializer.data)


  @detail_route(methods=['post'])
  def publish(self, request, pk):
    """
    A safe method to publish the story, only if the author is 
    """
    q =  self.queryset.filter(Q(owner=request.user) | Q(authors__user=request.user)).distinct()

    if pk.isdigit():
      story = get_object_or_404(q, pk=pk)
    else:
      story = get_object_or_404(q, slug=pk)

    if request.user.is_staff:
      story.status = Story.PUBLIC
    else:
      story.status = Story.PENDING
    story.save()
    serializer = LiteStorySerializer(story, context={'request': request})
    return Response(serializer.data)

    

  @detail_route(methods=['get'])
  def comments(self, request, pk=None):
    if pk.isdigit():
      sel = Q(story__pk=pk)
    else:
      sel = Q(story__slug=pk)

    coms = Comment.objects.exclude(status=Comment.DELETED).filter(sel)
    
    if request.user.is_staff:
      pass
    elif request.user.is_authenticated:
      # I amn the author of the ocomment OR I am the 
      coms = coms.filter(Q(story__owner=request.user) | Q(status=Comment.PUBLIC) | Q(story__authors__user=request.user)).distinct()
    else:
      coms = coms.filter(status=Comment.PUBLIC).filter(story__status=Story.PUBLIC).distinct()
    
    g = Glue(request=request, queryset=coms)

    page    = self.paginate_queryset(g.queryset)
    serializer = CommentSerializer(page, many=True, context={'request': request})
    return self.get_paginated_response(serializer.data)


  @detail_route(methods=['get'], url_path='git/diffs')
  def gitdiffs(self, request, pk): 
    q = self._getUserAuthorizations(request)
    
    if not pk.isdigit():
      story = get_object_or_404(q, slug=pk)
    else:
      story = get_object_or_404(q, pk=pk)

    serializer = LiteStorySerializer(story,
      context={'request': request},
    )
    d = serializer.data
    d['logs'] = story.gitLog()

    return Response(d)


  @detail_route(methods=['get'], url_path='git/blob/(?P<commit_id>[0-9a-f]+)')
  def gitblob(self, request, pk, commit_id=None):
    """
    e.g. http://localhost:8000/api/story/populism/git/blob/538d1420fbb0da6be027317d963c059e71b45de5/
    """
    q = self._getUserAuthorizations(request)
    
    if not pk.isdigit():
      story = get_object_or_404(q, slug=pk)
    else:
      story = get_object_or_404(q, pk=pk)

    contents = story.gitBlob(commit_id)

    serializer = StorySerializer(story,
      context={'request': request},
    )
    
    d = serializer.data
    d['contents'] = contents
    return Response(d)

  