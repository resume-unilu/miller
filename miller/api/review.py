from django.db.models import Q
from django.shortcuts import get_object_or_404


from rest_framework import serializers,viewsets
from rest_framework.exceptions import NotAuthenticated
from rest_framework.decorators import detail_route, permission_classes, list_route, detail_route
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from miller.api.serializers import ReviewSerializer, LiteReviewSerializer
from miller.models import Review, Author



class ReviewViewSet(viewsets.ModelViewSet):
  """
  Model viewset related to Review model.
  Default mixin get, post delete are for admin only.
  """
  queryset = Review.objects.all()
  serializer_class = ReviewSerializer
  permission_classes = (IsAuthenticated,)

  #@permission_classes(IsAdminUser)
  def create(self, request, *args, **kwargs):
    """
    Only staff can create reviews
    """
    if not request.user.is_staff:
      # it seems that the permission_classes is not working
      #       @permission_classes((IsAdminUser,))
      # TypeError: 'tuple' object is not callable
      raise NotAuthenticated()
    super(ReviewViewSet, self).create(self, request, *args, **kwargs)


  def partial_update(self, request, *args, **kwargs):
    """
    Request user can partial update reviews they have been assigned
    """
    review = get_object_or_404(self.queryset.filter(assignee=request.user), pk=kwargs['pk'])
    return super(ReviewViewSet, self).partial_update(request, *args, **kwargs)

  
  def list(self, request, *args, **kwargs):
    """
    This is the list of your reviews. Access to the uncompleted list via todo
    """
    qs = self.queryset.filter(assignee=request.user)
    page    = self.paginate_queryset(qs)
    serializer = LiteReviewSerializer(qs, many=True, context={'request': request})
    return self.get_paginated_response(serializer.data)

  
  def get(self, request, pk, *args, **kwargs):
    """
    List the reviews assigned to the request user. It requires an authentified user.
    """
    review = get_object_or_404(self.queryset.filter(assignee=request.user), pk=pk)
    
    serializer = ReviewSerializer(review,
        context={'request': request},
    )
    return Response(serializer.data)


  @detail_route(methods=['get'])
  def report(self, request, *args, **kwargs):
    """
    Only authors can access review report ;-)
    """
    review = get_object_or_404(self.queryset.exclude(status__in=[Review.INITIAL, Review.DRAFT]).filter(Q(story__authors__user=request.user) | Q(assignee=request.user)), pk=kwargs['pk'])
    serializer = ReviewSerializer(review,
      context={'request': request},
    )
    return Response(serializer.data)


  @list_route(methods=['get'])
  def reports(self, request):
    """
    Only authors can see reviews reports ;-)
    """
    qs = self.queryset.exclude(status__in=[Review.INITIAL, Review.DRAFT]).filter(Q(story__authors__user=request.user) | Q(assignee=request.user))
    page    = self.paginate_queryset(qs)
    serializer = LiteReviewSerializer(qs, many=True, context={'request': request})
    return self.get_paginated_response(serializer.data)