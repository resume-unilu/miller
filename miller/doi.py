import requests, logging, re

from django.conf import settings
from requests.exceptions import ConnectionError, HTTPError
from rest_framework.exceptions import ValidationError, APIException, AuthenticationFailed, NotFound, PermissionDenied, ParseError


logger = logging.getLogger('miller.doi')

def urlize(*args):
    return '/'.join(s.strip('/') for s in filter(lambda x: isinstance(x, basestring), args))


class ServiceUnavailable(APIException):
  status_code = 503
  default_detail = 'Service temporarily unavailable, try again later.'
  default_code = 'service_unavailable'


class DataciteDOI():
  prefix    = settings.MILLER_DOI_PREFIX
  publisher = settings.MILLER_DOI_PUBLISHER
  publisherprefix = settings.MILLER_DOI_PUBLISHER_PREFIX
  endpoint  = urlize(settings.MILLER_DOI_ENDPOINT, 'doi')
  auth      = settings.MILLER_DOI_AUTH
  baseurl   = settings.MILLER_DOI_HOST 

  def __init__(self, story):
    self.story   = story
    self.id      = None
    self._id     = story.data.get('doi', self.format())
    self._url = '%s/' % urlize(self.baseurl, 'story', story.slug)
    
  def cite(self, contentType="text/x-bibliography" ,style='apa', locale='fr-FR'):
    """
    Return a formatted version of the doi, if the doi is registered.
    Check https://citation.crosscite.org/docs.html for the different versions
    """
    url = urlize(settings.MILLER_DOI_RESOLVER, self._id)
    print 'MILLER_DOI_RESOLVER', contentType, style, locale
    try:
      res = requests.get(url=url, headers={
        'accept': '%s; style=%s; locale=%s' % (contentType, style, locale)
      })
    except ConnectionError as e:
      logger.exception(e)
      raise ServiceUnavailable()
    else:
      logger.debug('%s GET %s received %s' % (self._log_prefix(), url, res.status_code))
    

    try:
      res.raise_for_status()
    except HTTPError as e:
      if res.status_code == 404:
        raise NotFound()
      raise e

    logger.debug('%s'% res.headers)
    return res.text



  def config(self):
    return {
      'enabled': settings.MILLER_DOI_ENABLED,
      'baseurl': self.baseurl,
      
      'endpoint':    self.endpoint,
      'publisher':    self.publisher,
      'prefix': self.prefix
    }

  def format(self):
    return urlize(self.prefix, '%s-%s-%s' % (self.publisherprefix, self.story.short_url, self.story.date_created.year))

  @staticmethod
  
  def list(self):
    pass

  def _log_prefix(self):
    return 'doi {_id: %s, id:%s}' % (self._id, self.id)

  def create(self):
    """
    Return a doi representation, if any was created. 
    Raise exception otherwise.
    """
    logger.debug('%s with data: {doi: %s, url:%s}'% (self._log_prefix(), self._id, self._url))
    data = '#Content-Type:text/plain;charset=UTF-8\ndoi= %s\nurl= %s'% (self._id, self._url)
    # {
    #  'doi': self._id,
    #  'url': self._url
    #}
    res = self.perform_request(path=self._id, method='put', data=data, headers={
      "Content-Type":"text/plain;charset=UTF-8"
    })

    #print res.text
    return res


  def retrieve(self):
    """
    Retrieve XML metadata.
    """
    res = self.perform_request(path=self._id, headers={
      'Content-Type': 'application/xml',
      'charset': 'UTF-8'
    }, method='GET')
    return res.text
    

  def perform_request(self, data=None, method='get', headers=None, path=None):
    """
    Perform request against dooi api endpoint and raise REST Framework exceptions
    """
    if not settings.MILLER_DOI_ENABLED:
      logger.warning('Unable to load DOI, check settings.MILLER_DOI_ENABLED')
      raise NotFound()

    url = urlize(self.endpoint, path)
    #logger.debug('%s: %s %s' % (self._log_prefix(), method.upper(), url))
    

    try:
      
      res = getattr(requests, method.lower())(url=url, data=data, auth=self.auth, headers=headers)
    except ConnectionError as e:
      logger.exception(e)
      raise NotFound({
        'error': 'ConnectionError',
        'errorDescription': 'Service not ready. ConnectionError %s' % e    
      })
    except:
      logger.exception(e)
      raise e
    else:
      logger.debug('%s %s %s received %s' % (self._log_prefix(), method.upper(), url, res.status_code))

    try:
      res.raise_for_status()
    except HTTPError as e:
      
      if res.status_code == 400:
        logger.error('%s error:"%s"' % (self._log_prefix(), res.text))
        raise ValidationError({
            'error': res.text,
            'value': data,
            'endpoint': url
          })
      elif res.status_code == 401:
        raise AuthenticationFailed({
          'details': 'unable to authenticate against `datacite.org` DOI service',
          'config': self.config()
        })
      elif res.status_code == 404:
        raise NotFound({
          'error': 'NotFound',
          'doi': self._id
        })
      else:
        logger.exception(e)
        raise e
    
    return res



class DataciteDOIMetadata(DataciteDOI):
  endpoint  = urlize(settings.MILLER_DOI_ENDPOINT, 'metadata')

  def serialize(self, contentType='xml'):
    """
    Return a serialized version of the dictionary given
    """
    authors = self.story.authors.all()

    supervisors = self.story.owner.authorship.exclude(pk__in=authors.values_list('pk',flat=True))[0:1]

    publicationYear = '%s' % (self.story.date_created.year if self.story.date_created.year != self.story.date.year else self.story.date.year)

    contents = {
      'DOI': self._id,
      'creators': u''.join([author.asXMLCreator() for author in authors]),
      'contributors': u''.join([author.asXMLContributor(contributorType="Supervisor") for author in supervisors]),
      'title': self.story.get_DOI_title(),
      'publisher': self.publisher,
      'publicationYear': '%s' % self.story.date_created.year,
      'lastUpdate': '%s' % self.story.date_last_modified.strftime('%Y-%m-%d'),
      'resourceTypeGeneral': 'Text',
      'resourceType': 'article',
      'abstract': self.story.abstract,
      'subjects': u''.join([u''.join(tag.asXMLSubjects()) for tag in self.story.tags.filter(category__in=settings.MILLER_DOI_TAG_CATEGORIES_FOR_SUBJECT)]),
      'url': self._url
    }
    
    if contentType == 'xml':
      xml = u"""
          <?xml version="1.0" encoding="UTF-8"?>
        <resource xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://datacite.org/schema/kernel-4" xsi:schemaLocation="http://datacite.org/schema/kernel-4 http://schema.datacite.org/meta/kernel-4/metadata.xsd">
          <identifier identifierType="DOI">%(DOI)s</identifier>
          <creators>%(creators)s</creators>
          <contributors>%(contributors)s</contributors>
          <titles>
            <title>%(title)s</title>
          </titles>
          <publisher>%(publisher)s</publisher>
          <publicationYear>%(publicationYear)s</publicationYear>
          <resourceType resourceTypeGeneral="%(resourceTypeGeneral)s">%(resourceType)s</resourceType>
          <dates>
            <date dateType="Updated">%(lastUpdate)s</date>
          </dates>
          <descriptions><description descriptionType="Abstract">%(abstract)s</description></descriptions>
          <subjects>%(subjects)s</subjects>
          <alternateIdentifiers>
            <alternateIdentifier alternateIdentifierType="URL">%(url)s
            </alternateIdentifier>
          </alternateIdentifiers>
        </resource> """ % contents

      return re.sub(r'\n\s+','', xml.strip().encode('utf-8'))
    elif contentType == 'json':
      contents.update({
        'creators': [author.asDictCreator() for author in authors],
        'contributors': [author.asDictContributor(contributorType="Supervisor") for author in supervisors],
      })
      import json
      from django.core.serializers.json import DjangoJSONEncoder
      return json.dumps(contents, cls=DjangoJSONEncoder)

    return None


  def create(self):
    """
    Send an xml representing the metadata
    """
    
    res = self.perform_request(data=self.serialize(), headers={
      'Content-Type': 'application/xml',
      'charset': 'UTF-8'
    }, method='POST')
    return res.text



