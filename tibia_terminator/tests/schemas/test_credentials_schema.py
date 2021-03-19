#!/usr/bin/env python3.8

import unittest

from unittest import TestCase

from tibia_terminator.schemas.credentials_schema import CredentialSchema, CredentialsSchema


class TestCredentialsSchema(TestCase):
    def test_gets_values(self):
        # given
        json_dict = {
            "credentials": [
                {
                    "user": "test_user_1",
                    "password": "test_password_1",
                    "recovery_key": None
                },
                {
                    "user": "test_user_2",
                    "password": "test_password_2",
                },
                {
                    "user": "test_user_3",
                    "password": "test_password_3",
                    "recovery_key": "test_recovery_key"
                }
            ]
        }
        # when
        credentials = CredentialsSchema.load(json_dict)
        # then
        self.assertIsInstance(credentials, CredentialsSchema)
        self.assertCountEqual(credentials.credentials, 3)


if __name__ == '__main__':
    unittest.main()
