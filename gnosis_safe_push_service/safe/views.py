from django.conf import settings
from django.http import JsonResponse
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from gnosis_safe_push_service.version import __version__

from .serializers import AuthSerializer, PairingSerializer


def about_view(_):
    return JsonResponse({
        'version': __version__,
        'settings': {
            'ETH_HASH_PREFIX ': settings.ETH_HASH_PREFIX,
        }
    })


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


class PairingCreationView(CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = PairingSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)
