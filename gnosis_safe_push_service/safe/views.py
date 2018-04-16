from django.conf import settings
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from gnosis_safe_push_service.version import __version__

from .serializers import AuthSerializer, PairingSerializer


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
