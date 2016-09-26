
from django.conf  import settings
from django.contrib.syndication.views import Feed
from miller.models import Story

class LatestEntriesFeed(Feed):
    title = "Police beat site news"
    link = "/sitenews/"
    description = "Updates on changes and additions to police beat central."

    def items(self):
        return Story.objects.filter(status=Story.PUBLIC).order_by('-date_created')[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.abstract

   