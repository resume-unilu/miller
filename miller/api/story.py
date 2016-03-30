import json
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import serializers,viewsets
from rest_framework.response import Response

from miller.models import Story

# Serializers define the API representation.
class StorySerializer(serializers.HyperlinkedModelSerializer):
  class Meta:
    model = Story
    fields = ('id','url', 'short_url', 'title', 'abstract', 'contents', 'date', 'status', 'cover')


    
# ViewSets define the view behavior. Filter by status
class StoryViewSet(viewsets.ModelViewSet):
  queryset = Story.objects.all()
  serializer_class = StorySerializer


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
    
    stories = self.queryset.filter(Q(owner=request.user) | Q(status=Story.PUBLIC)).filter(**filters)
    page    = self.paginate_queryset(stories)

    serializer = self.serializer_class(stories, many=True,
        context={'request': request}
    )
    return self.get_paginated_response(serializer.data)

  def retrieve(self, request, pk=None):
    queryset = self.queryset.filter(pk=pk).filter(Q(owner=request.user) | Q(status=Story.PUBLIC))
    story = get_object_or_404(queryset, pk=pk)

    # // serialize with text content

    serializer = self.serializer_class(story,
        context={'request': request}
    )
    return Response(serializer.data)