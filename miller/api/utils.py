import json, re
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldError


waterfallre = re.compile(r'^_*')


class Glue():
  def __init__(self, request, queryset):
    self.filters, self.filtersWaterfall = filtersFromRequest(request=request)
    self.excludes, self.excludesWaterfall = filtersFromRequest(request=request, field_name='exclude')
    self.ordering = orderbyFromRequest(request=request)
    self.queryset = queryset
    self.warnings = None
    try:
      self.queryset = self.queryset.exclude(**self.excludes).filter(**self.filters)
    except FieldError as e:
      self.warnings = {
        'filters': '%s' % e
      }
      pass
    except TypeError as e:
      pass

    # apply filters progressively
    for fil in self.filtersWaterfall:
      print fil
      try:
        self.queryset = self.queryset.filter(**fil)
      except FieldError as e:
        pass
      except TypeError as e:
        pass


    if self.ordering is not None:
      self.queryset = self.queryset.order_by(*self.validated_ordering())
      
  def validated_ordering(self):
    _validated_ordering = []
    for field in self.ordering:
      _field = field.replace('-', '')
      _reverse = field.startswith('-')
      try:
        self.queryset.model._meta.get_field(_field)
      except Exception as e:
        self.warnings = {
          'ordering': '%s' % e
        }
      else:
       _validated_ordering.append('%s%s'%('-' if _reverse else '', _field))
    return _validated_ordering

# usage in viewsets.ModelViewSet methods, e;g. retrieve: 
# filters = filtersFromRequest(request=self.request) 
# qs = stories.objects.filter(**filters).order_by(*orderby)
def filtersFromRequest(request, field_name='filters'):
  filters = request.query_params.get(field_name, None)
  waterfall = []
  if filters is not None:
    try:
      filters = json.loads(filters)
      # print "filters,",filters
    except Exception, e:
      print e
      filters = {}
  else:
    filters = {}
  # filter filters having AND__ prefixes (cascade stuffs)
  for k,v in filters.items():
    if k.startswith('_'):
      waterfall.append({
        waterfallre.sub('', k): v
      })
      # get rifd of dirty filters
      filters.pop(k, None)

  return filters, waterfall


# usage in viewsets.ModelViewSet methods, e;g. retrieve: 
# orderby = orderbyFromRequest(request=self.request) 
# qs = stories.objects.all().order_by(*orderby)
def orderbyFromRequest(request):
  orderby = request.query_params.get('orderby', None)
  return orderby.split(',') if orderby is not None else None

# get corresponding serializer class to content_type.model property. `content_type` is instance of django.contrib.contenttypes.models.ContentType 
# https://docs.djangoproject.com/en/1.10/ref/contrib/contenttypes/#django.contrib.contenttypes.models.ContentType  
def get_serializer(content_type):
  # map of model names / serializers class
  if content_type.model == 'user':
    from miller.api.serializers import UserSerializer
    serializer = UserSerializer
  elif content_type.model == 'document':
    from miller.api.serializers import LiteDocumentSerializer
    serializer = LiteDocumentSerializer
  elif content_type.model == 'story':
    from miller.api.serializers import IncrediblyLiteStorySerializer
    serializer = IncrediblyLiteStorySerializer
  elif content_type.model == 'profile':
    from miller.api.serializers import ProfileSerializer
    serializer = ProfileSerializer
  elif content_type.model == 'comment':
    from miller.api.serializers import CommentSerializer
    serializer = CommentSerializer
  if not serializer:
    # raise
    return None
  return serializer


def get_serialized(instance):
  content_type  = ContentType.objects.get_for_model(instance)
  serializer = get_serializer(content_type)
  if serializer is None:
    return None
  return serializer(instance).data