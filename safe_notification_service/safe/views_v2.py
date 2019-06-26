from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from .serializers import AuthV2ResponseSerializer, AuthV2Serializer
from .services.auth_service import AuthServiceProvider


class AuthCreationView(CreateAPIView):
    serializer_class = AuthV2Serializer
    response_serializer = AuthV2ResponseSerializer

    @swagger_auto_schema(responses={201: response_serializer(),
                                    400: 'Invalid data'})
    def post(self, request, *args, **kwargs):
        """
        Links a `push_token` to one or more `owner` and register information of the device.
        If this endpoint is called again with the same `owner`, it will be updated with the new `push_token`
        {
          "push_token": "<string>",
          "build_number": "<integer>",
          "version_name": "<string>",
          "client": "[android | ios | extension]",
          "bundle": "<string>",
          "signatures": [
            {
              "v": "<integer>",
              "r": "<stringified int>",
              "s": "<stringified int>"
            },
          ]
        }
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            devices = AuthServiceProvider().create_auth(push_token=data['push_token'],
                                                        build_number=data['build_number'],
                                                        version_name=data['version_name'],
                                                        client=data['client'],
                                                        bundle=data['bundle'],
                                                        owners=data['signing_addresses'])

            response_serializer = self.response_serializer(devices, many=True)
            return Response(status=status.HTTP_201_CREATED, data=response_serializer.data)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer.errors)
