import json

from django.shortcuts import get_object_or_404

from rest_framework import serializers, viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from miller.api.fields import OptionalFileField, JsonField
from miller.models import Document, Story, Caption
from miller.forms import CaptionForm



# Serializers define the API representation.
class CaptionSerializer(serializers.ModelSerializer):
  class Meta:
    model = Caption
    fields = ('document', 'story', 'date_created')
    


# ViewSets define the view behavior. Filter by status
class CaptionViewSet(viewsets.ModelViewSet):

  queryset = Caption.objects.all()
  serializer_class = CaptionSerializer

  def create(self, request, *args, **kwargs):
    # get the document id from the slug
    form = CaptionForm(request.data)

    if not form.is_valid():
      raise ValidationError(form.errors) 

    god  = { 'pk': form.cleaned_data['document']} if form.cleaned_data['document'].isdigit() else { 'slug': form.cleaned_data['document'] }
    gos  = { 'pk': form.cleaned_data['story']} if form.cleaned_data['story'].isdigit() else { 'slug': form.cleaned_data['story'] }
    
    doc = get_object_or_404(Document, **god);
    story = get_object_or_404(Story, **gos)

    # Create the book instance
    caption, created = Caption.objects.get_or_create(document=doc, story=story)
    # print caption, created

    serializer = CaptionSerializer(caption)
    return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    #return caption

