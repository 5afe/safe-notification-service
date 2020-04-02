from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand

import requests
from requests import RequestException

from ....version import __version__


class Command(BaseCommand):
    help = 'Send slack notification'

    def handle(self, *args, **options):
        app_name = apps.get_app_config('safe').verbose_name
        startup_message = f'Starting {app_name} version {__version__}'
        self.stdout.write(self.style.SUCCESS(startup_message))

        if settings.SLACK_API_WEBHOOK:
            try:
                r = requests.post(settings.SLACK_API_WEBHOOK, json={'text': startup_message})
                if r.ok:
                    self.stdout.write(self.style.SUCCESS(f'Slack configured, "{startup_message}" sent'))
                else:
                    raise RequestException()
            except RequestException as e:
                self.stdout.write(self.style.ERROR(f'Cannot send slack notification to webhook ({settings.SLACK_API_WEBHOOK}): "{e}"'))
        else:
            self.stdout.write(self.style.SUCCESS('Slack not configured, ignoring'))
