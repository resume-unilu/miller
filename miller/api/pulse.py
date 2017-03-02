from rest_framework import serializers,viewsets
from actstream.models import any_stream, user_stream

from django.shortcuts import get_object_or_404
from django.utils import timezone
from miller.api.serializers import ActionSerializer
from actstream.models import Action

from rest_framework.response import Response
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated



class PulseViewSet(viewsets.GenericViewSet):
  """
  User notification API.
  """
  queryset = Action.objects.all()
  permission_classes = (IsAuthenticated,)
  serializer_class = ActionSerializer
  

  def list(self, request):
    """
    list everything if staff;
    list everything onnected to your follows otherwise
    """
    if request.user.is_staff: 
      queryset = self.queryset.exclude(actor_object_id=request.user.pk)
    else:
      queryset = user_stream(request.user).exclude(actor_object_id=request.user.pk)
    
    page    = self.paginate_queryset(queryset)
    serializer = ActionSerializer(page, many=True, context={'request': request})

    return self.get_paginated_response(serializer.data)


  @list_route(methods=['get'])
  def unread(self, request):
    """
    get just unread things count
    """
    if request.user.is_staff: 
      queryset = self.queryset.exclude(actor_object_id=request.user.pk)
    else:
      queryset = user_stream(request.user).exclude(actor_object_id=request.user.pk)

    queryset = queryset.filter(timestamp__gte=request.user.profile.date_last_notified)

    return Response({"count": queryset.count()})


  @list_route(methods=['get'])
  def noise(self, request):
    """
    what other people are doing?
    """
    if request.user.is_staff: 
      queryset = self.queryset.exclude(actor_object_id=request.user.pk)
    else:
      queryset = user_stream(request.user).exclude(actor_object_id=request.user.pk)

    queryset = queryset.filter(timestamp__gte=request.user.profile.date_last_notified)
    
    page    = self.paginate_queryset(queryset)
    serializer = ActionSerializer(page, many=True, context={'request': request})

    return self.get_paginated_response(serializer.data)


  @list_route(methods=['post'])
  def reset(self, request):
    """
    reset unread counter
    """
    request.user.profile.date_last_notified = timezone.now()
    request.user.profile.save()
    return Response({"message": "date last notified updated"})