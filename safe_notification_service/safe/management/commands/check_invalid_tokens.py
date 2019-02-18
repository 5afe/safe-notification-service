from django.core.management.base import BaseCommand

from safe_notification_service.firebase.client import (FirebaseProvider,
                                                       MockedClient)

from ...models import Device


class Command(BaseCommand):
    help = 'Check status of Firebase push tokens and return not valid ones'

    def add_arguments(self, parser):
        parser.add_argument('--delete', help='Remove tokens not valid', action='store_true')

    def handle(self, *args, **options):
        delete = options['delete']
        firebase_client = FirebaseProvider()
        if isinstance(firebase_client, MockedClient):
            self.stdout.write(self.style.ERROR('Firebase provider not configured!'))
        else:
            for device in Device.objects.all():
                if not device.push_token:
                    continue
                if not firebase_client.verify_token(device.push_token):
                    self.stdout.write(self.style.SUCCESS('Push-token={} is not valid anymore').format(device.push_token))
                    if delete:
                        device.push_token = None
                        device.save()
