from __future__ import absolute_import
# from jsonschema import Draft4Validator, validators
# from jsonschema.exceptions import ValidationError
from gnosis_safe_push_service.schema_validator.validator import Validator
from django.test import TestCase
import json


class TestValidator(TestCase):

    def test_validator_extension(self):
        schema = None

        with open('data/test_schema.json') as f:
            schema = json.load(f)

        valid_data = {
            "type": "safeCreation",
            "params": {
                "safe": "0x0",
                "deployer": "0x0"
            }
        }

        invalid_data = {
            "params": {
                "safe": "0x0",
                "deployer": "0x0"
            }
        }
        validator = Validator()
        validator.load_schema(schema)

        # TODO ADD CHECKS