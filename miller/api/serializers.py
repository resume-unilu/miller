from django.contrib.auth.models import User
from rest_framework import serializers
from miller.models import Profile, Document, Tag, Story
from miller.api.fields import JsonField, HitField

# serializer the authors.
class AuthorSerializer(serializers.ModelSerializer):
  class Meta:
    model = User
    fields = ('id', 'username', 'first_name', 'last_name', 'is_staff', 'url')


# tag represnetation in many to many
class TagSerializer(serializers.ModelSerializer):
  class Meta:
    model = Tag
    fields = ('id', 'category', 'name', 'status')



class UserSerializer(serializers.ModelSerializer):
  class Meta:
    model = User
    fields = ('username', 'first_name', 'last_name', 'is_staff')


# story serializer for tags
class ProfileSerializer(serializers.ModelSerializer):
  user = UserSerializer()
  username    = serializers.ReadOnlyField(source='user.username')
  
  class Meta:
    model = Profile
    lookup_field = 'user__username'
    fields = ('bio', 'picture', 'username', 'user')


# light document serializer (to be used in manytomany retrieve)
class LiteDocumentSerializer(serializers.ModelSerializer):
  metadata = JsonField(source='contents')

  class Meta:
    model = Document
    fields = ('id', 'copyrights', 'metadata', 'url', 'attachment')

# Story serializer containing whoosh matches
class MatchingStorySerializer(serializers.HyperlinkedModelSerializer):
  authors = AuthorSerializer(many=True)
  owner = AuthorSerializer()
  tags = TagSerializer(many=True)
  covers = LiteDocumentSerializer(many=True)
  matches = HitField()

  def is_named_bar(self, foo):
      return foo.name == "bar" 

  class Meta:
    model = Story
    fields = ('id', 'url', 'slug', 'short_url', 'title', 'abstract', 'date',  'date_created', 'status', 'covers', 'authors', 'tags', 'owner', 'matches')

