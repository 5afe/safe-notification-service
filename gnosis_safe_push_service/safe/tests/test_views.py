import json

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .factories import get_push_token, get_signature


class TestViews(APITestCase):

    def test_auth_creation(self):
        push_token = get_push_token()
        signature = get_signature(push_token)
        auth_data = {
            'pushToken': push_token,
            'signature': signature
        }

        request = self.client.post(reverse('api:auth-creation'), data=json.dumps(auth_data),
                                   content_type='application/json')
        self.assertEquals(request.status_code, status.HTTP_200_OK)

    def test_auth_fail(self):
        request = self.client.post(reverse('api:auth-creation'), data=json.dumps({}),
                                   content_type='application/json')
        self.assertEquals(request.status_code, status.HTTP_400_BAD_REQUEST)
