from django.contrib.sitemaps import Sitemap
from miller.models import Story



class NewsSitemap(Sitemap):
  changefreq = "never"
  priority = 0.5

  def items(self):
    return Story.objects.filter(tags__category='blog', status=Story.PUBLIC).distinct().order_by('-date_last_modified').prefetch_related('tags')

  def lastmod(self, obj):
    return obj.date_last_modified



class WritingsSitemap(Sitemap):
  changefreq = "never"
  priority = 0.5

  def items(self):
    return Story.objects.filter(tags__category='writing', status=Story.PUBLIC).distinct().order_by('-date').prefetch_related('tags')

  def lastmod(self, obj):
    return obj.date_last_modified


sitemaps = {
  'news': NewsSitemap,
  'writings': WritingsSitemap
}