from django.test import TestCase

from ..helpers import validate_google_billing_purchase
from .factories import get_google_billing_test_data


class TestHelpers(TestCase):

    def test_validate_google_billing_purchase(self):
        # Use data from google play test app
        app_public_key, purchase_json, purchase_signature = get_google_billing_test_data()

        self.assertTrue(validate_google_billing_purchase(app_public_key, purchase_json, purchase_signature))

        self.assertFalse(validate_google_billing_purchase(app_public_key, purchase_json, purchase_signature.upper()))

        self.assertFalse(validate_google_billing_purchase(app_public_key, purchase_json.upper(), purchase_signature))
