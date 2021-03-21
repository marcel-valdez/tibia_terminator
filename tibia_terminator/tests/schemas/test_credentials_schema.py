#!/usr/bin/env python3.8

import unittest

from unittest import TestCase
from typing import Iterable

from tibia_terminator.schemas.credentials_schema import (CredentialsSchema,
                                                         Credential)


class TestCredentialsSchema(TestCase):
    def test_gets_values(self):
        # given
        data = {
            "credentials": [{
                "user": "test_user_1",
                "password": "test_password_1",
                "recovery_key": None
            }, {
                "user": "test_user_2",
                "password": "test_password_2",
            }, {
                "user": "test_user_3",
                "password": "test_password_3",
                "recovery_key": "test_recovery_key"
            }]
        }
        target = CredentialsSchema()
        # when
        credentials = target.load(data)
        # then
        self.assertEqual(len(credentials), 3)
        self.assertIsInstance(credentials, Iterable)
        for i in range(3):
            self.assertIsInstance(credentials[i], Credential)
            self.assertEqual(credentials[i].user,
                             data["credentials"][i].get("user"))
            self.assertEqual(credentials[i].password,
                             data["credentials"][i].get("password"))
            self.assertEqual(credentials[i].recovery_key,
                             data["credentials"][i].get("recovery_key"))

    def test_gets_unknown_values(self):
        # given
        data = {
            "credentials": [{
                "user": "test_user_3",
                "password": "test_password_3",
                "recovery_key": "test_recovery_key",
                "other_value": "some_value"
            }]
        }
        target = CredentialsSchema()
        # when
        credentials = target.load(data)
        # then
        self.assertEqual(len(credentials), 1)
        self.assertIsInstance(credentials, Iterable)
        json_credential = data["credentials"][0]
        credential = credentials[0]
        self.assertIsInstance(credential, Credential)
        self.assertEqual(credential.user, json_credential.get("user"))
        self.assertEqual(credential.password, json_credential.get("password"))

    def test_get_by_user(self):
        # given
        data = {
            "credentials": [{
                "user": "other_user",
                "password": "other_password",
            }, {
                "user": "test_user_3",
                "password": "test_password_3",
            }]
        }
        target = CredentialsSchema()
        # when
        credentials = target.load(data)
        # then
        json_credential = data["credentials"][1]
        credential = credentials.get("test_user_3")
        self.assertIsInstance(credential, Credential)
        self.assertEqual(credential.user, json_credential.get("user"))
        self.assertEqual(credential.password, json_credential.get("password"))


if __name__ == '__main__':
    unittest.main()
