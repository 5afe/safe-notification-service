from django.conf import settings
from safe_service.safe.utils import singleton
from firebase_admin import credentials, initialize_app, messaging


@singleton
class FirebaseClient:

    def __init__(self, credentials):
        self._credentials = credentials
        self._authenticate()

    def _authenticate(self):
        self._auth_instance = credentials.Certificate(self._credentials)
        self._app = initialize_app(self._auth_instance)

    @property
    def auth_provider(self):
        return self._auth_instance

    def send_message(self, data):
        message = messaging.Message(
            data=data,
            token=settings.FIREBASE_API_KEY_TOKEN
        )
        response = messaging.send(message)
        return response