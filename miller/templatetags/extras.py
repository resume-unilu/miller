from django import template

register = template.Library()


@register.filter()
def lookup(obj):
  return 'ciao'