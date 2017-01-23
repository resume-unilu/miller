from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from miller.models import Story



class NewsSitemap(Sitemap):
  changefreq = "never"
  priority = 0.5
  protocol = settings.MILLER_HOST_PROTOCOL

  def items(self):
    return Story.objects.filter(tags__category='blog', status=Story.PUBLIC).distinct().order_by('-date_last_modified').prefetch_related('tags')

  def lastmod(self, obj):
    return obj.date_last_modified



class WritingsSitemap(Sitemap):
  changefreq = "never"
  priority = 0.5
  protocol = settings.MILLER_HOST_PROTOCOL

  def items(self):
    return Story.objects.filter(tags__category='writing', status=Story.PUBLIC).distinct().order_by('-date').prefetch_related('tags')

  def lastmod(self, obj):
    return obj.date_last_modified



class PagesSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'
    protocol = settings.MILLER_HOST_PROTOCOL
    
    def items(self):
        return settings.MILLER_STATIC_PAGES

    def location(self, item):
        return reverse('accessibility_page', kwargs={'page':item})


sitemaps = {
  'news': NewsSitemap,
  'writings': WritingsSitemap,
  'pages': PagesSitemap
}