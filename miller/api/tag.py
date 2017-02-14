import json

from django.db.models import Count

from rest_framework import serializers,viewsets

from miller.api.fields import JsonField
from miller.api.serializers import TagSerializer
from miller.api.utils import Glue, filtersFromRequest
from miller.models import Tag, Story

from rest_framework.decorators import api_view, list_route

# story serializer for tags
class StorySerializer(serializers.ModelSerializer):
  class Meta:
    model = Tag
    fields = ('url', 'title', 'date')


# ViewSets define the view behavior. Filter by status
class TagViewSet(viewsets.ModelViewSet):
  queryset = Tag.objects.all()
  serializer_class = TagSerializer

  def list(self, request):
    filters, _filters = filtersFromRequest(request=self.request)
    
    if request.user.is_authenticated() and request.user.is_staff:
      tags = Tag.objects.filter(**filters)
    else:
      tags = Tag.objects.filter(category=Tag.KEYWORD).filter(**filters)

    page    = self.paginate_queryset(tags)

    serializer = TagSerializer(tags, many=True,
        context={'request': request}
    )
    return self.get_paginated_response(serializer.data)


  @list_route(methods=['get'])
  def hallOfFame(self, request):
    g = Glue(request=self.request, queryset=Story.objects.all())
    
    if not request.user.is_staff:
      g.filters.update({'status':Story.PUBLIC})
    
    # horrible workaround.
    ids = g.queryset.values('pk')
    # print ids
    tag__filters, tf = filtersFromRequest(request=self.request, field_name='tag__filters')

    if g.ordering is None:
      g.ordering = ['-num_stories']
    # print filters
    # top n authors, per story filters.
    top_tags = Tag.objects.filter(**tag__filters).filter(story__pk__in=[s['pk'] for s in ids]).annotate(
      num_stories=Count('story', distinct=True)
    ).order_by(**g.ordering)
    
    page    = self.paginate_queryset(top_tags)
    serializer = self.serializer_class(page, many=True, context={'request': request})
    return self.get_paginated_response(serializer.data)
