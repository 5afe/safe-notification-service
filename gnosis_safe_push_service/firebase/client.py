from firebase_admin import credentials, initialize_app, messaging

from gnosis_safe_push_service.utils.singleton import singleton


@singleton
class FirebaseClient:

    def __init__(self, credentials, *args, **kwargs):
        self._credentials = credentials
        self._authenticate(*args, **kwargs)

    def _authenticate(self, *args, **kwargs):
        if isinstance(self._credentials, dict):
            self._auth_instance = credentials.Certificate(self._credentials)
            self._app = initialize_app(self._auth_instance, *args, **kwargs)
        else:
            self._app = initialize_app(self._credentials, *args, **kwargs)

    @property
    def auth_provider(self):
        return self._auth_instance

    @property
    def app(self):
        return self._app

    def send_message(self, data, token):
        """
        Sends a JSON message to Firebase
        :param data: JSON object
        :param token: Firebase token
        :return:
        """
        message = messaging.Message(
            data=data,
            token=token
        )
        response = messaging.send(message)
        return response
