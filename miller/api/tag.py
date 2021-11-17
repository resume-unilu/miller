import json

from django.conf import settings
from django.db.models import Count

from rest_framework import serializers, viewsets, status
from rest_framework.response import Response

from miller.api.fields import JsonField
from miller.api.serializers import TagSerializer
from miller.api.utils import Glue, filters_from_request
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
    if request.query_params.get('used_keywords', False):
      sort_method = request.query_params.get('statistics_sort', 'usage_statistics')
      if sort_method not in ('usage_statistics', 'euro_usage_statistics'):
        sort_method = 'usage_statistics'
      tags = Tag.objects.filter(category='keyword', usage_statistics__gt=0).order_by('-{}'.format(sort_method))

    elif request.query_params.get('used_keywords_splitted', False):
      tags = Tag.objects.filter(category='keyword')
      if not request.user.is_staff:
        tags = tags.filter(category__in=settings.MILLER_NON_STAFF_TAG_CATEGORIES)

      limit = int(request.query_params.get('limit', 20))
      euro_tags = [(t, t.euro_usage_statistics) for t in tags.filter(euro_usage_statistics__gt=0).order_by('-euro_usage_statistics')[:limit]]
      global_tags = [(t, t.usage_statistics) for t in tags.filter(usage_statistics__gt=0).order_by('-usage_statistics')[:limit]]

      res = []
      for tag, _ in sorted(euro_tags + global_tags, lambda a, b: a[1] > b[1]):
        if tag not in res:
          res.append(tag)

      page = self.paginate_queryset(res)
      serializer = TagSerializer(page, many=True, context={'request': request})
      return self.get_paginated_response(serializer.data)

    else:
      tags = Tag.objects.all()

    if not request.user.is_staff:
      tags = tags.filter(category__in=settings.MILLER_NON_STAFF_TAG_CATEGORIES)

    g = Glue(request=request, queryset=tags)
    page    = self.paginate_queryset(g.queryset)

    serializer = TagSerializer(page, many=True,
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
    tag__filters, tf = filters_from_request(request=self.request, field_name='tag__filters')

    if g.ordering is None:
      g.ordering = ['-num_stories']
    # print filters
    # top n authors, per story filters.
    top_tags = Tag.objects.filter(**tag__filters).filter(story__pk__in=[s['pk'] for s in ids]).annotate(
      num_stories=Count('story', distinct=True)
    ).order_by(*g.ordering)
    
    page    = self.paginate_queryset(top_tags)
    serializer = self.serializer_class(page, many=True, context={'request': request})
    return self.get_paginated_response(serializer.data)
