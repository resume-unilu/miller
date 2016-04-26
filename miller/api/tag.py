import json
from rest_framework import serializers,viewsets
from miller.models import Tag, Story
from rest_framework.decorators import api_view

# story serializer for tags
class StorySerializer(serializers.ModelSerializer):
  class Meta:
    model = Tag
    fields = ('url', 'title', 'date')

# Serializers define the API representation.
class TagSerializer(serializers.HyperlinkedModelSerializer):
  class Meta:
    model = Tag
    fields = ('id', 'url','name', 'category')
    

# ViewSets define the view behavior. Filter by status
class TagViewSet(viewsets.ModelViewSet):
  stories = StorySerializer(many=True)


  queryset = Tag.objects.all()
  serializer_class = TagSerializer

  def list(self, request):
    filters = self.request.query_params.get('filters', None)
    
    if filters is not None:
      print filters
      try:
        filters = json.loads(filters)
        # print "filters,",filters
      except Exception, e:
        # print e
        filters = {}
    else:
      filters = {}
    # print filters
    # retrieve only good filters
    if request.user.is_authenticated() and request.user.is_staff:
      tags = Tag.objects.filter(**filters)
    else:
      tags = Tag.objects.filter(category__in='keyword').filter(**filters)

    page    = self.paginate_queryset(tags)

    serializer = TagSerializer(tags, many=True,
        context={'request': request}
    )
    return self.get_paginated_response(serializer.data)