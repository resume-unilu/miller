from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser

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