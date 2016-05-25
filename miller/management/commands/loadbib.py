import bibtexparser, json
from django.db.utils import IntegrityError
from django.utils.text import slugify
from django.core.management.base import BaseCommand, CommandError
from miller.models import Document, Profile

class Command(BaseCommand):
    help = 'Load a .bib database file exported from zotero and save each entry as a separate Document'

    def add_arguments(self, parser):
        parser.add_argument('filepath', nargs='+', type=str)

    def handle(self, *args, **options): 
      filepath = '/Users/danieleguido/Documents/resume/zotero.bib'
      
      owner = Profile.objects.filter(user__is_staff=True)[0]
      print owner.user
      Document.objects.filter(type=Document.BIBLIOGRAPHIC_REFERENCE).delete()
      with open(filepath) as bibtex_file:
        bibtex_database = bibtexparser.load(bibtex_file)
        self.stdout.write(self.style.SUCCESS('Successfully imported bibtex file "%s"' % filepath))

        total = len(bibtex_database.entries)
        
        for index, ref in enumerate(bibtex_database.entries):
          # unicity given by link
          slug = 'bibtex/' + slugify(' '.join([ref['title'],  ref['year'] if 'year' in ref else '']).strip())[:100]
          title = ref['title']
          if 'link' in ref:
            self.stdout.write('%s of %s' % (index+1, total))
            self.stdout.write('saving %(ID)s %(link)s...' % ref)
            try:
              doc, created = Document.objects.get_or_create(type=Document.BIBLIOGRAPHIC_REFERENCE, url=ref['link'], defaults={
                'title': title,
                'slug': slug,
                'owner': owner.user
              })
            except IntegrityError, e:
              self.stdout.write(self.style.ERROR('FAILED "%s"' % ref['title']))
              continue

            if created:
              self.stdout.write(self.style.SUCCESS('OK'))
            else:
              self.stdout.write(self.style.SUCCESS('UP'))
            
            
          else :
            try:
              doc, created = Document.objects.get_or_create(type=Document.BIBLIOGRAPHIC_REFERENCE, slug=slug, defaults={
                'title': ref['title'],
                'owner': owner.user
              })
            except IntegrityError, e:
              self.stdout.write(self.style.ERROR('FAILED "%s"' % ref['title']))
              break
            # self.stdout.write(self.style.WARNING('FAILED, link not found "%s"' % ref['title']))
            #break

          doc.contents = json.dumps(ref)
          doc.save()
          #print ref