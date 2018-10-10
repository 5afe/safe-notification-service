from django.test import TestCase

from safe_notification_service.firebase.client import FirebaseClient

from .utils import MessagingService, MockCredential, send_message


class TestFirebase(TestCase):

    def setUp(self):
        creds = MockCredential()
        self.firebase_client = FirebaseClient(creds, {'projectId': 'mock-project-id'})
        self.firebase_client.send_message = send_message
        self.firebase_messaging = MessagingService(self.firebase_client.app)

    def test_authentication(self):
        self.assertEqual(self.firebase_client._app._project_id, 'mock-project-id')

    def test_send_message(self):
        response = self.firebase_client.send_message(message_instance=self.firebase_messaging,
                                                     data={'value': 'mock-value'},
                                                     token='mock-token')
        self.assertIsNotNone(response)
