from rest_framework import serializers,viewsets
from rest_framework.decorators import detail_route

from miller.api.serializers import ProfileSerializer, LiteAuthorSerializer
from miller.models import Profile, Author

# ViewSets define the view behavior. Filter by status
class ProfileViewSet(viewsets.ModelViewSet):
  queryset = Profile.objects.all()
  serializer_class = ProfileSerializer
  lookup_field = 'user__username'
  lookup_value_regex = '[0-9a-zA-Z\.\-_]+'

  @detail_route(methods=['get'])
  def authors(self, request, *args, **kwargs):
    print kwargs
    authors = Author.objects.filter(user__username=kwargs['user__username'])
    page    = self.paginate_queryset(authors)
    serializer = LiteAuthorSerializer(authors, many=True, context={'request': request})
    return self.get_paginated_response(serializer.data)


  @detail_route(methods=['get'])
  def pulse(self, request, pk):
    print 'here'
    pass