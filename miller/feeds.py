
from django.conf  import settings
from django.contrib.syndication.views import Feed
from miller.models import Story

class LatestEntriesFeed(Feed):
    title = settings.RSS_TITLE
    link = "/latest/feed/"
    description = settings.RSS_DESCRIPTION

    def items(self):
        return Story.objects.filter(status=Story.PUBLIC).order_by('-date_created')[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.abstract

    def item_author_name(self, item):
        return u''.join([u'%s %s' %(a.first_name, a.last_name) for a in item.authors.all()])

    def get_context_data(self, **kwargs):
        context = super(LatestEntriesFeed, self).get_context_data(**kwargs)
        context['foo'] = 'bar'
        return context