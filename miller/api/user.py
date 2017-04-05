from rest_framework import viewsets
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from django.contrib.auth.models import User

from miller.api.serializers import UserSerializer

from utils import Glue



# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
  queryset = User.objects.all()
  serializer_class = UserSerializer
  permission_classes = (IsAdminUser,)


  def list(self, request):
    g = Glue(request=request, queryset=self.queryset)
    print g.filters
    users = g.queryset

    page    = self.paginate_queryset(users)
    serializer = UserSerializer(page, many=True, context={'request': request})
    return self.get_paginated_response(serializer.data)


  @list_route(methods=['get'], permission_classes=[IsAuthenticated])
  def reviewers(self, request):
    if not request.user.groups.filter(name='chief-reviewers').exists():
      # check 
      raise PermissionDenied()
    users   = self.queryset.filter(groups__name='reviewers')
    page    = self.paginate_queryset(users)
    serializer = UserSerializer(page, many=True, context={'request': request})
    return self.get_paginated_response(serializer.data)