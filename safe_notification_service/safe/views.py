from django.conf import settings
from django.db.models import Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from safe_notification_service.safe.models import Device, DevicePair
from safe_notification_service.version import __version__

from .serializers import (AuthResponseSerializer, AuthSerializer,
                          NotificationSerializer, PairingDeletionSerializer,
                          PairingResponseSerializer, PairingSerializer, SimpleNotificationSerializer)


class AboutView(APIView):
    renderer_classes = (JSONRenderer,)

    def get(self, request, format=None):
        content = {
            'version': __version__,
            'api_version': self.request.version,
            'https_detected': self.request.is_secure(),
            'settings': {
                'ETH_HASH_PREFIX ': settings.ETH_HASH_PREFIX,
                'FIREBASE_CREDENTIALS_PATH': settings.FIREBASE_CREDENTIALS_PATH,
                'NOTIFICATION_MAX_RETRIES': settings.NOTIFICATION_MAX_RETRIES,
                'NOTIFICATION_RETRY_DELAY_SECONDS': settings.NOTIFICATION_RETRY_DELAY_SECONDS,
            }
        }
        return Response(content)


class AuthCreationView(CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = AuthSerializer

    @swagger_auto_schema(responses={201: AuthResponseSerializer(),
                                    400: 'Invalid data'})
    def post(self, request, *args, **kwargs):
        """
        Links a `push_token` to a `owner`. If this endpoint is called again with the same `owner`,
        it will be updated with the new `push_token`
        """
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid():
            device = serializer.save()
            response_serializer = AuthResponseSerializer(data={
                'owner': device.owner,
                'push_token': device.push_token
            })
            assert response_serializer.is_valid()
            return Response(status=status.HTTP_201_CREATED, data=response_serializer.data)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)


class PairingView(CreateAPIView):
    permission_classes = (AllowAny,)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PairingSerializer
        elif self.request.method == 'DELETE':
            return PairingDeletionSerializer

    def handle_exception(self, exc):
        if isinstance(exc, Device.DoesNotExist):
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        else:
            raise exc

    @swagger_auto_schema(responses={201: PairingResponseSerializer(),
                                    400: 'Invalid data'})
    def post(self, request, *args, **kwargs):
        """
        Pairs 2 devices
        """
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid():
            instance = serializer.save()
            response_serializer = PairingResponseSerializer(data={
                'device_pair': [instance.authorizing_device.owner,
                                instance.authorized_device.owner]
            })
            assert response_serializer.is_valid()
            return Response(status=status.HTTP_201_CREATED, data=response_serializer.data)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)

    @swagger_auto_schema(responses={204: 'Pair was deleted',
                                    400: 'Invalid data'})
    def delete(self, request, *args, **kwargs):
        """
        Delete pairing between 2 devices
        """
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid():
            signer_address = serializer.validated_data['signing_address']
            device_address = serializer.validated_data['device']

            pairings = DevicePair.objects.filter(
                (Q(authorizing_device__owner=signer_address) | Q(authorized_device__owner=device_address))
            )

            pairings.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)


class NotificationView(CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = NotificationSerializer

    @swagger_auto_schema(responses={204: 'Notification was queued',
                                    400: 'Invalid data',
                                    404: 'No pairing found'})
    def post(self, request, *args, **kwargs):
        """
        Send notification to device/s
        """
        serializer = self.get_serializer_class()(data=request.data)
        if serializer.is_valid():
            if serializer.save():
                # At least one pairing found
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)


class SimpleNotificationView(NotificationView):
    serializer_class = SimpleNotificationSerializer
