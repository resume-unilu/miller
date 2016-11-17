from django.contrib.auth.models import User
from rest_framework import serializers
from miller.models import Profile, Document, Tag, Story, Caption, Mention, Author
from miller.api.fields import JsonField, HitField, OptionalFileField



class CaptionSerializer(serializers.HyperlinkedModelSerializer):
  document_id    = serializers.ReadOnlyField(source='document.id')
  type  = serializers.ReadOnlyField(source='document.type')
  title = serializers.ReadOnlyField(source='document.title')
  slug  = serializers.ReadOnlyField(source='document.slug')
  src   = OptionalFileField(source='document.attachment')
  short_url = serializers.ReadOnlyField(source='document.short_url')
  copyrights = serializers.ReadOnlyField(source='document.copyrights')
  caption = serializers.ReadOnlyField(source='contents')
  metadata = JsonField(source='document.contents')
  snapshot = OptionalFileField(source='document.snapshot', read_only=True)

  class Meta:
    model = Caption
    fields = ('id', 'document_id', 'title', 'slug', 'type', 'copyrights', 'caption', 'short_url', 'src', 'snapshot', 'metadata')



class UserSerializer(serializers.ModelSerializer):
  class Meta:
    model = User
    fields = ('username', 'first_name', 'last_name', 'is_staff')

# serializer the authors.
class AuthorSerializer(serializers.ModelSerializer):
  user = UserSerializer()
  metadata = JsonField()
  class Meta:
    model = Author
    fields = ('id', 'user', 'fullname', 'affiliation', 'metadata')


# tag represnetation in many to many
class TagSerializer(serializers.ModelSerializer):
  class Meta:
    model = Tag
    fields = ('id', 'category', 'slug', 'name', 'status')





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
    fields = ('id', 'metadata', 'url', 'attachment', 'slug')


class LiteMentionSerializer(serializers.ModelSerializer):
  slug     = serializers.ReadOnlyField()
  metadata = JsonField()
  covers   = LiteDocumentSerializer(many=True)
  tags = TagSerializer(many=True)
  class Meta:
    model = Mention
    fields = ('id', 'slug', 'metadata', 'covers', 'tags')




# Story Serializer to use in lists
class LiteStorySerializer(serializers.HyperlinkedModelSerializer):
  authors = AuthorSerializer(many=True)
  owner = UserSerializer()
  tags = TagSerializer(many=True)
  covers = LiteDocumentSerializer(many=True)
  metadata = JsonField()

  class Meta:
    model = Story
    fields = ('id','url', 'slug', 'short_url', 'date',  'date_created', 'date_last_modified', 'status', 'covers', 'authors', 'tags', 'owner', 'metadata')


# retrieve a Story, full
class StorySerializer(serializers.HyperlinkedModelSerializer):
  authors = AuthorSerializer(many=True)
  owner = UserSerializer()
  tags = TagSerializer(many=True)
  documents = CaptionSerializer(source='caption_set', many=True)
  covers = LiteDocumentSerializer(many=True)
  stories = LiteMentionSerializer(many=True)
  metadata = JsonField()

  class Meta:
    model = Story
    fields = (
      'id','url','slug','short_url',
      'title', 'abstract',
      'documents', 'tags', 'covers', 'stories',
      'metadata',
      'contents',
      'date', 'date_created', 
      'status', 
      'authors','owner'
    )


# Story serializer containing whoosh matches
class MatchingStorySerializer(serializers.HyperlinkedModelSerializer):
  authors = AuthorSerializer(many=True)
  owner = UserSerializer()
  tags = TagSerializer(many=True)
  covers = LiteDocumentSerializer(many=True)
  matches = HitField()
  metadata = JsonField()

  def is_named_bar(self, foo):
      return foo.name == "bar" 

  class Meta:
    model = Story
    fields = ('id', 'url', 'slug', 'short_url', 'title', 'abstract', 'date',  'date_created', 'status', 'covers', 'metadata', 'authors', 'tags', 'owner', 'matches')



# Serializer when creating stories. It automatically add the owner as author
class CreateStorySerializer(serializers.ModelSerializer):
  owner = serializers.HiddenField(
    default=serializers.CurrentUserDefault()
  )

  class Meta:
    model = Story
    fields='__all__'



##############
# Collection #
##############

# A story of stories
class CollectionSerializer(serializers.ModelSerializer):
  authors = AuthorSerializer(many=True)
  stories = LiteMentionSerializer(many=True)
  owner = UserSerializer()
  tags = TagSerializer(many=True)
  covers = LiteDocumentSerializer(many=True)
  documents = CaptionSerializer(source='caption_set', many=True)
  metadata = JsonField()

  class Meta:
    model = Story
    fields = ('id', 'status', 'title', 'covers', 'authors', 'owner', 'tags', 'documents', 'stories', 'metadata', 'contents')



############
# Document #
############

# Serializers define the API representation.
class DocumentSerializer(serializers.ModelSerializer):
  # authors = AuthorSerializer(many=True)
  # owner = UserSerializer()
  # tags = TagSerializer(many=True)
  # captions = CaptionSerializer(source='caption_set', many=True)
  metadata = JsonField(source='contents')
  src   = OptionalFileField(source='attachment')
  snapshot = OptionalFileField(read_only=True)
  class Meta:
    model = Document
    fields = ('id', 'url', 'src', 'metadata', 'type', 'slug', 'title', 'snapshot', 'copyrights')


class MatchingDocumentSerializer(serializers.ModelSerializer):
  matches = HitField()
  metadata = JsonField(source='contents')
  src   = OptionalFileField(source='attachment')

  class Meta:
    model = Document
    fields = ('id', 'url', 'src', 'metadata', 'type', 'slug', 'title', 'metadata', 'matches')


# define the 
class CreateDocumentSerializer(serializers.ModelSerializer):
  metadata = JsonField(source='contents')
  owner = serializers.HiddenField(
    default=serializers.CurrentUserDefault()
  )
  snapshot = OptionalFileField(read_only=True)

  class Meta:
    model = Document
    fields = ('id', 'owner', 'type','short_url', 'title', 'slug', 'metadata', 'copyrights', 'url', 'attachment', 'snapshot')
  

  # def create(self, validated_data):
  #   print 'CREATING', validated_data

  #   # owner =  validated_data.pop('owner')
  #   # print owner.id
  #   if not 'url' in validated_data:
  #     return super(CreateDocumentSerializer, self).create(validated_data)

  #   print 'url:', validated_data['url']
  #   # get object
  #   try:
  #     doc = Document.objects.get(url=validated_data['url'])
  #   except Document.DoesNotExist:
  #     print "not found, create"
  #     return super(CreateDocumentSerializer, self).create(validated_data)
  #   else:
  #     return doc
    # print "found doc", doc
    # instance, _ = Document.objects.get_or_create(url=validated_data['url'], defaults=validated_data)
    
    # return instance
    
    

############
# Mentions #
############
class MentionSerializer(serializers.ModelSerializer):
  to_story = LiteStorySerializer()
  from_story     = LiteStorySerializer()

  class Meta:
    model = Mention
    fields = ('id', 'to_story', 'from_story')

