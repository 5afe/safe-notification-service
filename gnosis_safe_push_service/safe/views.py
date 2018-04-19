from django.conf import settings
from django.db.models import Q
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from gnosis_safe_push_service.safe.models import DevicePair
from gnosis_safe_push_service.version import __version__

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
            serializer.save()
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)
