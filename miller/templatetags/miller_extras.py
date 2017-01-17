import re
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe
from markdown import markdown
from markdown.extensions import Extension


register = template.Library()

class MagicLinks(Extension):
  def extendMarkdown(self, md, md_globals):
    print 'exted!!!!!!!!!!!', md.inlinePatterns['link']

@register.simple_tag()
def publication_title():
  return settings.MILLER_TITLE
  

@register.simple_tag()
def lookup(obj, path, language):
  desiredLanguage = [item[2] for item in settings.LANGUAGES if item[0] == language][0]
  defaultLanguage = [item[2] for item in settings.LANGUAGES if item[0] == settings.LANGUAGE_CODE][0]

  contents = obj.get(path, {})

  if desiredLanguage in contents:
    return contents[desiredLanguage]
  if defaultLanguage in contents:
    return contents[defaultLanguage]

  return contents.itervalues().next()


@register.simple_tag()
def markdownit(text, language):
  desiredLanguage = [item[2] for item in settings.LANGUAGES if item[0] == language][0]
  defaultLanguage = [item[2] for item in settings.LANGUAGES if item[0] == settings.LANGUAGE_CODE][0]

  candidates = filter(None, re.split(r'<!--\s*(lang:[a-zA-Z_]{2,5})\s*-->', text))

  # print (zip(candidate, candidate))
  # candidate.length should be a multiple of 2
  if len(candidates) % 2 == 0:
    d  = {k:v for k,v in zip(*[iter(candidates)]*2)}
    k  = 'lang:%s' % desiredLanguage
    dk = 'lang:%s' % defaultLanguage
    if k in d:
      text = d[k]
    elif dk in d:
      text = d[dk]
    else:
      text = d.itervalues().next()


  return mark_safe(markdown(text, extensions=['footnotes', MagicLinks()]))



@register.filter()
def urled(url):
  return url.replace('accessibility/', '')


@register.simple_tag()
def qsfilter(qs, key, value):
  return qs.filter(**{key:value})


@register.filter()
def shorten(text, maxwords=5):
  if not text:
    return '';
  words = re.split(r'(?!=\.\s)\s', text)[:maxwords];

  sentence = ' '.join(words)

  if len(sentence) < len(text):
    # if(!sentence.match(/\?\!\.$/)){
    #   sentence += ' '
    # }
    
    sentence = '%s ...' % sentence
  return sentence;