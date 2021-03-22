#!/usr/bine/env python3.8


from marshmallow import fields, post_load, EXCLUDE
from typing import Optional, NamedTuple, List
from tibia_terminator.schemas.common import FactorySchema


class Credential(NamedTuple):
    user: str
    password: str
    recovery_key: Optional[str] = None


class Credentials(NamedTuple):
    credentials: List[Credential] = []

    def __iter__(self):
        return self.credentials.__iter__()

    def __len__(self) -> int:
        return len(self.credentials)

    def __getitem__(self, key: int):
        if not isinstance(key, int):
            raise Exception("Can only subscript by index")
        return self.credentials[key]

    def get(self, user: str) -> Optional[Credential]:
        for credential in filter(lambda c: c.user == user, self.credentials):
            return credential


class CredentialSchema(FactorySchema[Credential]):
    class Meta:
        unknown = EXCLUDE

    user = fields.Str(required=True)
    password = fields.Str(required=True)
    recovery_key = fields.Str(allow_none=True)

    @post_load
    def make_credential(self, data, **kwargs) -> Credential:
        return Credential(**data)


class CredentialsSchema(FactorySchema[Credentials]):
    credentials = fields.List(fields.Nested(CredentialSchema))

    @post_load
    def make_credentials(self, data, **kwargs) -> Credentials:
        return Credentials(**data)
