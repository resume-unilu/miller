import json
# usage in viewsets.ModelViewSet methods, e;g. retrieve: 
# filters = filtersFromRequest(request=self.request) 
# qs = stories.objects.filter(**filters).order_by(*ordering)
def filtersFromRequest(request):
  filters = request.query_params.get('filters', None)
    
  if filters is not None:
    try:
      filters = json.loads(filters)
      # print "filters,",filters
    except Exception, e:
      # print e
      filters = {}
  else:
    filters = {}

  return filters


# usage in viewsets.ModelViewSet methods, e;g. retrieve: 
# ordering = orderingFromRequest(request=self.request) 
# qs = stories.objects.all().order_by(*ordering)
def orderingFromRequest(request):
  ordering = request.query_params.get('ordering', None)
  return ordering.split(',') if ordering is not None else None