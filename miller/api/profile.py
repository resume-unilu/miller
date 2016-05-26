from rest_framework import serializers,viewsets

from miller.api.serializers import ProfileSerializer
from miller.models import Profile

# ViewSets define the view behavior. Filter by status
class ProfileViewSet(viewsets.ModelViewSet):
  queryset = Profile.objects.all()
  serializer_class = ProfileSerializer
  lookup_field = 'user__username'
  lookup_value_regex = '[0-9a-zA-Z\.-_]+'
  # def list(self, request):
  #   filters = self.request.query_params.get('filters', None)
    
  #   if filters is not None:
  #     print filters
  #     try:
  #       filters = json.loads(filters)
  #       # print "filters,",filters
  #     except Exception, e:
  #       # print e
  #       filters = {}
  #   else:
  #     filters = {}
  #   # print filters
  #   # retrieve only good filters
  #   if request.user.is_authenticated() and request.user.is_staff:
  #     tags = Tag.objects.filter(**filters)
  #   else:
  #     tags = Tag.objects.filter(category__in='keyword').filter(**filters)

  #   page    = self.paginate_queryset(tags)

  #   serializer = TagSerializer(tags, many=True,
  #       context={'request': request}
  #   )
  #   return self.get_paginated_response(serializer.data)