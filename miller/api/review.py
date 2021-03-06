from django.db.models import Q
from django.shortcuts import get_object_or_404


from rest_framework import serializers, viewsets, status
from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.decorators import detail_route, permission_classes, list_route, detail_route
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from miller.api.serializers import CreateReviewSerializer, ReviewSerializer, LiteReviewSerializer, AnonymousReviewSerializer, AnonymousLiteReviewSerializer
from miller.api.utils import Glue

from miller.models import Review, Author, Story



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
    if not request.user.is_staff and not request.user.groups.filter(name=Review.GROUP_CHIEF_REVIEWERS).exists():
      # check 
      raise PermissionDenied()
      # it seems that the permission_classes is not working
      #       @permission_classes((IsAdminUser,))
      # TypeError: 'tuple' object is not callable
    serializer = CreateReviewSerializer(data=request.data, context={'request': request}, partial=True)
    
    if not serializer.is_valid():
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    serializer.save(assigned_by=request.user)
    return Response(serializer.data)
    



  def partial_update(self, request, *args, **kwargs):
    """
    Request user can partial update reviews they have been assigned.
    Once the review status has been changed to COMPLETED/REJECTED/BOUNCE this method is no more available (a not found error is thrown) 
    """
    self.queryset = self.queryset.filter(status__in=[Review.INITIAL, Review.DRAFT], assignee=request.user)
    review = get_object_or_404(self.queryset, pk=kwargs['pk'])
    return super(ReviewViewSet, self).partial_update(request, *args, **kwargs)

  
  def list(self, request, *args, **kwargs):
    reviews = self.queryset.filter(assignee=request.user)
    g = Glue(queryset=reviews, request=request)
    #filters = filtersFromRequest(request=self.request)
    #ordering = orderbyFromRequest(request=self.request)
    """
    This is the list of your reviews. Access to the uncompleted list via todo
    """
    reviews = g.queryset

    page    = self.paginate_queryset(reviews)
    serializer = LiteReviewSerializer(page, many=True, context={'request': request})
    return self.get_paginated_response(serializer.data)

  
  def retrieve(self, request, pk, *args, **kwargs):
    """
    List the reviews assigned to the request user. It requires an authentified user.
    """
    if request.user.is_staff or request.user.groups.filter(name__in=[Review.GROUP_CHIEF_REVIEWERS, Review.GROUP_REVIEWERS, Review.GROUP_EDITORS]).exists():
      review = get_object_or_404(self.queryset, pk=pk)
    else:
      review = get_object_or_404(self.queryset.filter(assignee=request.user), pk=pk)
    
    serializer = ReviewSerializer(review,
        context={'request': request},
    )
    return Response(serializer.data)


  @list_route(methods=['post'])
  def close(self, request, *args, **kwargs):
    """
    Create a *special review* where the assignee and the assigned_by is the chief reviewer.
    Set the related story status to: REVIEW_DONE.
    test with `python manage.py miller.test.test_api_reviews.ReviewTest`
    cfr. `_test_close_review` method.
    """
    if not 'story' in request.data:
      return Response([], status=status.HTTP_400_BAD_REQUEST)

    if not request.user.groups.filter(name=Review.GROUP_CHIEF_REVIEWERS).exists():
      raise PermissionDenied()

    serializer = CreateReviewSerializer(data=request.data, context={'request': request}, partial=True)
    
    if not serializer.is_valid():
      return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    story = get_object_or_404(Story.objects.filter(status__in=[Story.REVIEW, Story.EDITING]).exclude(Q(authors__user=request.user) | Q(owner=request.user)), pk=request.data['story'])
    serializer.save(story=story,category=Review.CLOSING_REMARKS, assigned_by=request.user, assignee=request.user)
    return Response(serializer.data)


  #detail_route(methods=['get'], url_path='acceptance/(?P<hash>[0-9a-zA-Z]+)/(?P<consent>[0-9a-f]+)')
  @detail_route(methods=['get'], url_path='acceptance/(?P<assessment>(%s)+)' % '|'.join([i[0] for i in Review.ACCEPTANCE_CHOICES]))
  def acceptance(self, request, pk, assessment, *args, **kwargs):
    """
    Authentified user can accept review if review has not been accepted.
    Then the review assignee can follow the story.
    """
    review = get_object_or_404(Review.objects.filter(acceptance=Review.INITIAL).filter(assignee=request.user), pk=pk)

    from actstream.actions import follow
    review.acceptance = assessment;
    review.save()
    
    follow(review.assignee, review.story, actor_only=False)

    serializer = ReviewSerializer(review,
      context={'request': request},
    )
    return Response(serializer.data)


  @detail_route(methods=['get'])
  def report(self, request, *args, **kwargs):
    """
    Only authors can access review report ;-)
    """
    review = get_object_or_404(self.queryset.exclude(status__in=[Review.INITIAL, Review.DRAFT]).filter(Q(story__authors__user=request.user) | Q(assignee=request.user) | Q(assigned_by=request.user)), pk=kwargs['pk'])
    serializer =  ReviewSerializer(review,
      context={'request': request},
    ) if review.assignee.username == request.user.username else AnonymousReviewSerializer(review,
      context={'request': request},
    )
    return Response(serializer.data)


  @list_route(methods=['get'])
  def reports(self, request):
    """
    Only authors can see reviews reports ;-)
    """
    qs = self.queryset.exclude(status__in=[Review.INITIAL, Review.DRAFT]).filter(Q(story__authors__user=request.user))
    page    = self.paginate_queryset(qs)
    serializer = AnonymousLiteReviewSerializer(page, many=True, context={'request': request})
    return self.get_paginated_response(serializer.data)