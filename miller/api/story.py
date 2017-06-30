#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json, os, mimetypes

from collections import OrderedDict

from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Q
from django.http import StreamingHttpResponse
from django.shortcuts import get_object_or_404

from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAdminUser
from rest_framework.exceptions import PermissionDenied, ValidationError

from rest_framework import serializers,viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import  api_view, permission_classes, detail_route, list_route # cfr StoryViewSet

from miller.forms import GitTagForm
from miller.models import Story, Tag, Document, Caption, Comment, Review
from miller.api.utils import Glue
from miller.api.fields import OptionalFileField, JsonField
from miller.api.serializers import LiteDocumentSerializer, AnonymousStorySerializer, AnonymousLiteStorySerializer, MatchingStorySerializer, AuthorSerializer, TagSerializer, StorySerializer, LiteStorySerializer, CreateStorySerializer, CommentSerializer, PendingStorySerializer
from miller.api.pagination import VerbosePagination

from wsgiref.util import FileWrapper


# ViewSets define the view behavior. Filter by status
class StoryViewSet(viewsets.ModelViewSet):
  
  queryset = Story.objects.all()
  serializer_class = CreateStorySerializer
  pagination_class = VerbosePagination


  def _getUserAuthorizations(self, request):
    if request.user.is_staff:
      q = Story.objects.all()
    elif request.user.is_authenticated and request.user.groups.filter(name=Review.GROUP_CHIEF_REVIEWERS).exists():
      q = Story.objects.filter(Q(owner=request.user) | Q(authors__user=request.user) | Q(status__in=[Story.PUBLIC, Story.PENDING, Story.EDITING, Story.REVIEW, Story.REVIEW_DONE])).distinct()
    elif request.user.is_authenticated:
      q = Story.objects.filter(Q(owner=request.user) | Q(status=Story.PUBLIC) | Q(authors__user=request.user)).distinct()
    else:
      q = Story.objects.filter(status=Story.PUBLIC).distinct()
    return q


  def perform_create(self, serializer):
    uploaded = self.request.FILES['source'] if 'source' in self.request.FILES else False
    
    if uploaded:
      import pypandoc
      from tempfile import NamedTemporaryFile
      with NamedTemporaryFile() as f:
        for chunk in uploaded.chunks():
          f.write(chunk)
        f.seek(0)  # go back to the beginning of the file
        contents = pypandoc.convert_file(f.name, 'markdown', format='docx', extra_args=['--base-header-level=2', '--atx-headers'])
        from django.core.files import File
        #serializer.source.
        story = serializer.save(owner=self.request.user, contents=contents, source=uploaded)
        story.create_first_author()
        story.save()
        # save file separately
    else:
      story = serializer.save()
      story.create_first_author()
      story.save()
   
    # for filename, file in self.request.FILES.iteritems():
    #   print filename
    #   name = .name
    #   f = self.request.FILES[filename]
    #   with open('some/file/name.txt', 'wb+') as destination:
    #     for chunk in f.chunks():
    #         destination.write(chunk)

    

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

    ckey = story.get_cache_key()
    #transform contents if required.
    _parser = request.query_params.get('parser', None)
    if _parser:
      if _parser == 'yaml':
        import yaml
        try:
          story.contents = yaml.load(story.contents)
        except yaml.scanner.ScannerError as e:
          return Response({
            'parser': 'yaml',
            'field': 'contents',
            'error': '%s'%e
          })
        ckey = story.get_cache_key(extra=_parser)
    
    #print 'nocache:', request.query_params.get('nocache', None)
    #anonymize if story status is pending or under review (e.g. for chief reviewer)
    if story.status in (Story.PENDING, Story.REVIEW) and not story.authors.filter(user=request.user).exists() and request.user.groups.filter(name=Review.GROUP_CHIEF_REVIEWERS).exists():
      serializer = AnonymousStorySerializer(story,
        context={'request': request},
      )
      return Response(serializer.data)

    if not request.query_params.get('nocache', None) and cache.has_key(ckey):
      #print 'serve cahced', ckey
      return Response(cache.get(ckey))

    serializer = StorySerializer(story,
        context={'request': request},
    )
    d = serializer.data
    #print 'set cache', ckey
    cache.set(ckey, d)

    if request.query_params.get('nocache', None) and request.query_params.get('with-git-logs', None):
      d.update({
        'logs': story.get_git_tags_by_commit(commit_id=story.version)
      })
    
    
    return Response(d)
  

  def list(self, request):
    stories = self._getUserAuthorizations(request)
    g = Glue(request=request, queryset=stories)
    
    stories = g.queryset

    if 'status' not in g.filters:
      stories = stories.exclude(status=Story.DELETED)

    if g.warnings is not None:
      # this comes from the VerbosePagination class
      self.paginator.set_queryset_warnings(g.warnings)
      self.paginator.set_queryset_verbose(g.get_verbose_info())

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


    
    attachment = story.download(outputFormat='pdf')
    mimetype = mimetypes.guess_type(attachment)[0]
    # print attachment,mimetype
    
    response = StreamingHttpResponse(FileWrapper( open(attachment), 8192), content_type=mimetype)
    response['Content-Length'] = os.path.getsize(attachment)  
    response['Content-Disposition'] = 'attachment; filename="%s.%s"' % (story.slug,mimetypes.guess_extension(mimetype))
      
    return response


  @detail_route(methods=['get'], url_path='download/source')
  def downloadSource(self, request, pk):
    """
    This should work for the owner, the authro, the staff, chief-reviewers and reviewers only.
    """
    q = self.queryset.exclude(source__isnull=True)
    if not request.user.is_authenticated:
      raise PermissionDenied()
    elif request.user.is_staff or request.user.groups.filter(name=Review.GROUP_CHIEF_REVIEWERS).exists():
      pass
    else:
      q = self.queryset.filter(Q(owner=request.user) | Q(authors__user=request.user) | Q(reviews__assignee=request.user) | Q(reviews__assigned_by=request.user))

    story = get_object_or_404(q, pk=pk)
    mimetype = mimetypes.guess_type(story.source.path)[0]
    response = StreamingHttpResponse(FileWrapper( open(story.source.path), 8192), content_type=mimetype)
    response['Content-Length'] = os.path.getsize(story.source.path)  
    response['Content-Disposition'] = 'attachment; filename="%s.%s"' % (story.slug,mimetypes.guess_extension(mimetype))
    
    return response

  
  @list_route(methods=['get'])
  def search(self, request):
    """
    Add matches to the list of matching story.
    /api/document/?q=world
    cfr. utils.Glue class
    """
    from miller.forms import SearchQueryForm
    from miller.helpers import search_whoosh_index_headline
    form = SearchQueryForm(request.query_params)
    if not form.is_valid():
      return Response(form.errors, status=status.HTTP_201_CREATED)
    
    stories = self._getUserAuthorizations(request)
    # get the results
    g = Glue(request=request, queryset=stories)
    
    # queryset = g.queryset.annotate(matches=RawSQL("SELECT 
    page    = self.paginate_queryset(g.queryset.distinct())

    # get hort_url to get results out of whoosh
    highlights = search_whoosh_index_headline(query=form.cleaned_data['q'], paths=map(lambda x:x.short_url, page))

    def mapper(d):
      d.matches = []
      for hit in highlights:
        if d.short_url == hit['short_url']:
          d.matches = hit
          break
      return d

    serializer = MatchingStorySerializer(map(mapper, page), many=True,
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

  
  @list_route(methods=['get'])
  def featured(self, request):
    ckey = 'story.featured'
    if not request.query_params.get('nocache', None) and cache.has_key(ckey):
      # print 'serve cahced', ckey
      return Response({'results': cache.get(ckey)})
    
    stories = self.queryset.filter(status=Story.PUBLIC).filter(tags__slug='top', tags__category=Tag.HIGHLIGHTS)
    page    = self.paginate_queryset(stories)
    serializer = LiteStorySerializer(page, many=True, context={'request': request})

    # print 'set cache', ckey
    cache.set(ckey, serializer.data)
    return self.get_paginated_response(serializer.data)


  @list_route(methods=['get'])
  def pending(self, request):
    """
    Return a list of stories marked for reviews without assigned reviews.
    This is also accessible by reviewers.
    """
    if not request.user.is_authenticated or not request.user.groups.filter(name='chief-reviewers').exists():
      # check 
      raise PermissionDenied()

    qs = self.queryset.filter(status__in=[Story.PENDING, Story.REVIEW, Story.REVIEW_DONE, Story.EDITING]).exclude(authors__user=request.user).distinct()
    g = Glue(request=request, queryset=qs)

    # cannot get your own stories...
    page    = self.paginate_queryset(g.queryset)
    serializer = PendingStorySerializer(page, many=True, context={'request': request})
    return self.get_paginated_response(serializer.data)
    


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
      coms = coms.filter(Q(story__owner=request.user) | Q(status=Comment.PUBLIC) | Q(story__authors__user=request.user) | Q(story__reviews__assignee__username=request.user.username)).distinct()
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


  @detail_route(methods=['get'], url_path='git/diff/(?P<commit_id>[0-9a-f]+)')
  def git_diff(self, request, pk, commit_id=None):
    """
    Return a list of diffs
    e.g. http://localhost:8000/api/story/populism/git/diff/538d1420fbb0da6be027317d963c059e71b45de5/
    """
    q = self._getUserAuthorizations(request)
    
    if not pk.isdigit():
      story = get_object_or_404(q, slug=pk)
    else:
      story = get_object_or_404(q, pk=pk)
    
    results = story.get_git_diff(commit_id)
    return Response({
      # 'raw': story.get_git_contents_by_commit(commit_id),
      'results': results
    })


  @detail_route(methods=['get', 'post'], url_path='git/tag')
  def git_tags(self, request, pk): 
    if request.method == 'POST':
      form = GitTagForm(request.data)
      if not form.is_valid():
        raise ValidationError(form.errors)

    q = self._getUserAuthorizations(request)
    
    if not pk.isdigit():
      story = get_object_or_404(q, slug=pk)
    else:
      story = get_object_or_404(q, pk=pk)

    ckey = story.get_cache_key(extra='git_tags')

    if request.method == 'POST':
      # form is valid, and we have the right story loaded.
      if not request.user.is_authenticated:
        raise PermissionDenied()
      try:
        story.gitTag(tag=form.cleaned_data['tag'], message=form.cleaned_data['message'], raise_eception=True, author=request.user.username)
      except Exception as e:
        raise ValidationError({
          'tag': 'a version with this name exists already'
        })
      pass
    #elif cache.has_key(ckey):
    #  return Response(cache.get(ckey))
    # print 'oooallalala'
    d = story.get_git_tags()
    cache.set(ckey, d)
    
    return Response({
      'results': d
    })



  @detail_route(methods=['get'], url_path='git/tag/(?P<tag>[0-9a-z\.]+)')
  def git_blob_by_tag(self, request, pk, tag): 
    """
    Note: this accepts tag patterns and 
    """
    q = self._getUserAuthorizations(request)
    
    if not pk.isdigit():
      story = get_object_or_404(q, slug=pk)
    else:
      story = get_object_or_404(q, pk=pk)

    ckey = story.get_cache_key(extra='git_blob:%s' % tag)
    # if cache.has_key(ckey):
    #   return Response(cache.get(ckey))
    # # if tag is . something, try to get the 

    serializer = StorySerializer(story,
      context={'request': request},
    )
    
    d = serializer.data
    d['version']    = tag.split('.')[-1]
    d['logs']       = story.get_git_tags_by_commit(commit_id=d['version'])
    d['contents']   = story.get_git_contents_by_commit(tag);
    d['highlights'] = story.get_highlights_by_commit(tag)
    return Response(d)