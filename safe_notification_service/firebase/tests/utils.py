import json

from firebase_admin import _http_client, messaging
from firebase_admin.credentials import Base
from google.auth.credentials import Credentials
from requests import adapters, models

FIREBASE_AUTH_CREDENTIALS = {
    "type": "service_account",
    "project_id": "mock-project-id",
    "private_key_id": "mock-key-id-1",
    "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEAwJENcRev+eXZKvhhWLiV3Lz2MvO+naQRHo59g3vaNQnbgyduN/L4krlr\nJ5c6FiikXdtJNb/QrsAHSyJWCu8j3T9CruiwbidGAk2W0RuViTVspjHUTsIHExx9euWM0Uom\nGvYkoqXahdhPL/zViVSJt+Rt8bHLsMvpb8RquTIb9iKY3SMV2tCofNmyCSgVbghq/y7lKORt\nV/IRguWs6R22fbkb0r2MCYoNAbZ9dqnbRIFNZBC7itYtUoTEresRWcyFMh0zfAIJycWOJlVL\nDLqkY2SmIx8u7fuysCg1wcoSZoStuDq02nZEMw1dx8HGzE0hynpHlloRLByuIuOAfMCCYwID\nAQABAoIBADFtihu7TspAO0wSUTpqttzgC/nsIsNn95T2UjVLtyjiDNxPZLUrwq42tdCFur0x\nVW9Z+CK5x6DzXWvltlw8IeKKeF1ZEOBVaFzy+YFXKTz835SROcO1fgdjyrme7lRSShGlmKW/\nGKY+baUNquoDLw5qreXaE0SgMp0jt5ktyYuVxvhLDeV4omw2u6waoGkifsGm8lYivg5l3VR7\nw2IVOvYZTt4BuSYVwOM+qjwaS1vtL7gv0SUjrj85Ja6zERRdFiITDhZw6nsvacr9/+/aut9E\naL/koSSb62g5fntQMEwoT4hRnjPnAedmorM9Rhddh2TB3ZKTBbMN1tUk3fJxOuECgYEA+z6l\neSaAcZ3qvwpntcXSpwwJ0SSmzLTH2RJNf+Ld3eBHiSvLTG53dWB7lJtF4R1KcIwf+KGcOFJv\nsnepzcZBylRvT8RrAAkV0s9OiVm1lXZyaepbLg4GGFJBPi8A6VIAj7zYknToRApdW0s1x/XX\nChewfJDckqsevTMovdbg8YkCgYEAxDYX+3mfvv/opo6HNNY3SfVunM+4vVJL+n8gWZ2w9kz3\nQ9Ub9YbRmI7iQaiVkO5xNuoG1n9bM+3Mnm84aQ1YeNT01YqeyQsipP5Wi+um0PzYTaBw9RO+\n8Gh6992OwlJiRtFk5WjalNWOxY4MU0ImnJwIfKQlUODvLmcixm68NYsCgYEAuAqI3jkk55Vd\nKvotREsX5wP7gPePM+7NYiZ1HNQL4Ab1f/bTojZdTV8Sx6YCR0fUiqMqnE+OBvfkGGBtw22S\nLesx6sWf99Ov58+x4Q0U5dpxL0Lb7d2Z+2Dtp+Z4jXFjNeeI4ae/qG/LOR/b0pE0J5F415ap\n7Mpq5v89vepUtrkCgYAjMXytu4v+q1Ikhc4UmRPDrUUQ1WVSd+9u19yKlnFGTFnRjej86hiw\nH3jPxBhHra0a53EgiilmsBGSnWpl1WH4EmJz5vBCKUAmjgQiBrueIqv9iHiaTNdjsanUyaWw\njyxXfXl2eI80QPXh02+8g1H/pzESgjK7Rg1AqnkfVH9nrwKBgQDJVxKBPTw9pigYMVt9iHrR\niCl9zQVjRMbWiPOc0J56+/5FZYm/AOGl9rfhQ9vGxXZYZiOP5FsNkwt05Y1UoAAH4B4VQwbL\nqod71qOcI0ywgZiIR87CYw40gzRfjWnN+YEEW1qfyoNLilEwJB8iB/T+ZePHGmJ4MmQ/cTn9\nxpdLXA==\n-----END RSA PRIVATE KEY-----",
    "client_email": "mock-email@mock-project.iam.gserviceaccount.com",
    "client_id": "1234567890",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://accounts.google.com/o/oauth2/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/mock-project-id.iam.gserviceaccount.com"
}

FIREBASE_TOKEN = 'mock-token'


class MockHttpClient(_http_client.HttpClient):
    def request(self, method, url, **kwargs):
        return kwargs['json']

    def parse_body(self, resp):
        resp.update({'name': 'test-name'})
        return resp


class MockGoogleCredential(Credentials):
    """A mock Google authentication credential."""
    def refresh(self, request):
        self.token = 'mock-token'


class MockCredential(Base):
    """A mock Firebase credential implementation."""

    def __init__(self):
        self._g_credential = MockGoogleCredential()

    def get_credential(self):
        return self._g_credential


class MockAdapter(adapters.HTTPAdapter):
    """A mock HTTP adapter for the Python requests module."""
    def __init__(self, data, status, recorder):
        adapters.HTTPAdapter.__init__(self)
        self._data = data
        self._status = status
        self._recorder = recorder

    def send(self, request, **kwargs):
        request._extra_kwargs = kwargs
        self._recorder.append(request)
        resp = models.Response()
        resp.url = request.url
        resp.status_code = self._status
        resp.raw = self._data.encode()
        return resp


def send_message(*args, message_instance, data, token):
    message = messaging.Message(
        data=data,
        token=token
    )
    response = message_instance.send(message)
    return response


class MessagingService:

    _DEFAULT_RESPONSE = json.dumps({'name': 'message-id'})

    def __init__(self, app, *args, **kwargs):
        # self.fcm_service = messaging._get_messaging_service(app)
        # self.fcm_service._client.session.mount(
        #     'https://fcm.googleapis.com',
        #     MockAdapter(json.dumps({'name': 'message-id'}), 200, self.recorder)
        # )
        # super(MessagingService, self).__init__(app, *args, **kwargs)
        self.fcm_service, self.recorder = self._instrument_messaging_service(app)
        self.session = self.fcm_service._client.session
        self._client = MockHttpClient(session=self.session)
        self._fcm_url = 'https://fcm.googleapis.com/v1/projects/{0}/messages:send'.format(app.project_id)
        self._timeout = app.options.get('httpTimeout')

    def _instrument_messaging_service(self, app, status=200, payload=_DEFAULT_RESPONSE):
        fcm_service = messaging._get_messaging_service(app)
        recorder = []
        fcm_service._client.session.mount(
            'https://fcm.googleapis.com',
            MockAdapter(payload, status, recorder)
        )
        return fcm_service, recorder

    def send(self, message, dry_run=False):
        data = {'message': messaging._MessagingService.encode_message(message)}
        if dry_run:
            data['validate_only'] = True

        resp = self._client.body('post', url=self._fcm_url, json=data, timeout=self._timeout)
        return resp['name']
