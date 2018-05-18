from django.conf import settings
from django.db.models import Q
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from safe_notification_service.safe.models import Device, DevicePair
from safe_notification_service.version import __version__

from .serializers import (AuthSerializer, NotificationSerializer,
                          PairingDeletionSerializer, PairingSerializer)


class AboutView(APIView):
    renderer_classes = (JSONRenderer,)

    def get(self, request, format=None):
        content = {
            'version': __version__,
            'api_version': self.request.version,
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

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)


class PairingView(APIView):
    permission_classes = (AllowAny,)

    def handle_exception(self, exc):
        if isinstance(exc, Device.DoesNotExist):
            return Response(status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        else:
            raise exc

    def post(self, request, *args, **kwargs):
        serializer = PairingSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)

    def delete(self, request, *args, **kwargs):
        serializer = PairingDeletionSerializer(data=request.data)
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


class NotificationView(APIView):
    permission_classes = (AllowAny,)
    serializer_class = NotificationSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            if serializer.save():
                # At least one pairing found
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)
