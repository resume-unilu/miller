import json
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import serializers,viewsets, status
from rest_framework.response import Response

from miller.models import Story, Tag, Document, Caption


class OptionalFileField(serializers.Field):
  def to_representation(self, obj):
    if hasattr(obj, 'url'):
      return obj.url
    return None

class JsonField(serializers.Field):
  def to_representation(self, obj):
    if obj:
      try:
        return json.loads(obj)
      except ValueError:
        return obj
    return obj



class CaptionSerializer(serializers.HyperlinkedModelSerializer):
  document_id    = serializers.ReadOnlyField(source='document.id')
  type  = serializers.ReadOnlyField(source='document.type')
  title = serializers.ReadOnlyField(source='document.title')
  slug  = serializers.ReadOnlyField(source='document.slug')
  src   = OptionalFileField(source='document.attachment')
  short_url = serializers.ReadOnlyField(source='document.short_url')
  copyrights = serializers.ReadOnlyField(source='document.copyrights')
  caption = serializers.ReadOnlyField(source='contents')
  metadata = JsonField(source='document.contents')
  snapshot = serializers.ReadOnlyField(source='document.snapshot')

  class Meta:
    model = Caption
    fields = ('id', 'document_id', 'title', 'slug', 'type', 'copyrights', 'caption', 'short_url', 'src', 'snapshot', 'metadata')


# tag represnetation in many to many
class TagSerializer(serializers.ModelSerializer):
  class Meta:
    model = Tag
    fields = ('id', 'category', 'name', 'status')


# serializer the authors.
class AuthorSerializer(serializers.ModelSerializer):
  class Meta:
    model = User
    fields = ('id', 'username', 'first_name', 'last_name', 'is_staff', 'url')


# Serializers define the API representation.
class StorySerializer(serializers.HyperlinkedModelSerializer):
  authors = AuthorSerializer(many=True)
  owner = AuthorSerializer()
  tags = TagSerializer(many=True)
  documents = CaptionSerializer(source='caption_set', many=True)
  
  class Meta:
    model = Story
    fields = ('id','url', 'short_url', 'title', 'abstract', 'documents', 'contents', 'date', 'status', 'cover', 'cover_copyright', 'authors', 'tags', 'owner')


# Serializer to use in list of story items
class LiteStorySerializer(serializers.HyperlinkedModelSerializer):
  authors = AuthorSerializer(many=True)
  owner = AuthorSerializer()
  tags = TagSerializer(many=True)

  class Meta:
    model = Story
    fields = ('id','url', 'short_url', 'title', 'abstract', 'date', 'status', 'cover', 'cover_copyright', 'authors', 'tags', 'owner')


class CreateStorySerializer(serializers.ModelSerializer):
  owner = serializers.HiddenField(
    default=serializers.CurrentUserDefault()
  )

  class Meta:
    model = Story
    

# ViewSets define the view behavior. Filter by status
class StoryViewSet(viewsets.ModelViewSet):
  queryset = Story.objects.all()
  serializer_class = CreateStorySerializer


  def list(self, request):
    filters = self.request.query_params.get('filters', None)
    
    if filters is not None:
      print filters
      try:
        filters = json.loads(filters)
        print "filters,",filters
      except Exception, e:
        print e
        filters = {}
    else:
      filters = {}
    
    if request.user.is_authenticated():
      stories = self.queryset.filter(Q(owner=request.user) | Q(authors=request.user) | Q(status=Story.PUBLIC)).filter(**filters).distinct()
    else:
      stories = self.queryset.filter(status=Story.PUBLIC).filter(**filters).distinct()
    print stories.query
    page    = self.paginate_queryset(stories)

    serializer = LiteStorySerializer(stories, many=True,
        context={'request': request}
    )
    return self.get_paginated_response(serializer.data)


  
  
  def retrieve(self, request, pk=None):
    if request.user.is_authenticated():
      queryset = self.queryset.filter(Q(owner=request.user) | Q(authors=request.user) | Q(status=Story.PUBLIC)).distinct()
    else:
      queryset = self.queryset.filter(status=Story.PUBLIC).distinct()

    story = get_object_or_404(queryset, pk=pk)

    # // serialize with text conten

    serializer = StorySerializer(story,
        context={'request': request},
    )
    return Response(serializer.data)