from abc import ABC, abstractmethod
from logging import getLogger

from firebase_admin import credentials, initialize_app, messaging

from safe_notification_service.utils.singleton import singleton

logger = getLogger(__name__)


class MessagingClient(ABC):

    @property
    @abstractmethod
    def auth_provider(self):
        pass

    @property
    @abstractmethod
    def app(self):
        return self._app

    @abstractmethod
    def send_message(self, data, token):
        raise NotImplementedError


@singleton
class FirebaseClient(MessagingClient):
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
        logger.debug("Sending data=%s with token=%s", data, token)
        message = messaging.Message(
            data=data,
            token=token
        )
        response = messaging.send(message)
        return response


@singleton
class MockedClient(MessagingClient):
    @property
    def auth_provider(self):
        return None

    @property
    def app(self):
        return None

    def send_message(self, data, token):
        logger.warning("MockedClient: Not sending message with data %s and token %s", data, token)
        return 'MockedResponse'
