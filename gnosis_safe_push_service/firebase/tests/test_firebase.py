from django.test import TestCase
from gnosis_safe_push_service.firebase.client import FirebaseClient
from .utils import send_message, MessagingService, MockCredential


class TestFirebase(TestCase):

    def setUp(self):
        creds = MockCredential()
        self.firbClient = FirebaseClient(creds, {'projectId': 'mock-project-id'})
        self.firbClient.send_message = send_message
        self.firbMessaging = MessagingService(self.firbClient.app)

    def test_authentication(self):
        self.assertEquals(self.firbClient._app._project_id, 'mock-project-id')

    def test_send_message(self):
        response = self.firbClient.send_message(message_instance=self.firbMessaging, data={'value': 'mock-value'}, token='mock-token')
        self.assertIsNotNone(response)

