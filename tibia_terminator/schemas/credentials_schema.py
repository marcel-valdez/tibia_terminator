#!/usr/bine/env python3.8

from marshmallow import Schema, fields


class CredentialSchema(Schema):
    user = fields.Str(required=True)
    password = fields.Str(required=True)
    recovery_key = fields.Str(allow_none=True)


class CredentialsSchema(Schema):
    credentials = fields.List(fields.Nested(CredentialSchema))
