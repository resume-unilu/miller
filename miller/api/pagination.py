from collections import OrderedDict

from django.db.models import Count
from django.db.models.expressions import RawSQL
from django.contrib.postgres.fields import JSONField

from rest_framework.pagination import LimitOffsetPagination
from rest_framework.response import Response


class FacetedPagination(LimitOffsetPagination):

    facets_queryset = None

    def paginate_queryset(self, queryset, request, view=None):
      self.facets_queryset = queryset
      return super(FacetedPagination, self).paginate_queryset(queryset, request, view=view)

    def get_paginated_response(self, data):
      return Response(OrderedDict([
          ('count', self.count),
          ('next', self.get_next_link()),
          ('previous', self.get_previous_link()),
          ('results', data),
          ('facets', self.get_facets()),
      ]))

    def get_facets(self):

      facets = self.request.query_params.getlist("facets", [])
      out_facets = {}

      for facet in facets:
          json_field = False
          pieces = facet.split("__")
          if len(pieces) > 1:
            fieldname = pieces[0]
            field_instance = self.facets_queryset.model._meta.get_field(fieldname)
            if isinstance(field_instance, JSONField):
                json_field = True
          if json_field:
            rawsql_field = "((%s->>%%s))" % fieldname
            subfield = ("__").join(pieces[1:])
            annotate_dict = { facet : RawSQL(rawsql_field, (subfield,)) }
            counts = self.facets_queryset.annotate(**annotate_dict)\
                .values(facet).annotate(count=Count(facet)).order_by(facet)
          else:
            counts = self.facets_queryset.values(facet).annotate(count=Count(facet)).order_by(facet)
          out_facets[facet] = counts
      return out_facets
