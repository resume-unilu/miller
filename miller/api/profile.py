from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework import serializers,viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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
    authors = Author.objects.filter(user__username=kwargs['user__username'])
    page    = self.paginate_queryset(authors)
    serializer = LiteAuthorSerializer(authors, many=True, context={'request': request})
    return self.get_paginated_response(serializer.data)


  @detail_route(methods=['get'])
  def pulse(self, request, pk):
    print 'here'
    pass


  @list_route(methods=['get'], permission_classes=[IsAuthenticated])
  def me(self, request):
    pro = get_object_or_404(self.queryset, user__username=request.user.username)
    serializer =  self.serializer_class(pro)
    _d = serializer.data

    _d.update({
      'settings': settings.MILLER_SETTINGS
    })
    return Response(_d)