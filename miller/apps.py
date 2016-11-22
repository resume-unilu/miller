from django.apps import AppConfig

class ActivityStreamConfig(AppConfig):
    name = 'miller'
    verbose_name = 'The Miller Platform'

    def ready(self):
      from actstream import registry
      registry.register(self.get_model('Story'))
      registry.register(self.get_model('Document'))
      registry.register(self.get_model('Profile'))


