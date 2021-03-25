#!/usr/bin/env python3.8

import unittest

from unittest import TestCase
from typing import NamedTuple, Optional
from marshmallow import Schema, fields, post_load, ValidationError
from tibia_terminator.schemas.common import (ResolvableField)


class TestResult(NamedTuple):
    ref_field: int
    test_field: int
    optional_ref_field: Optional[int] = None
    optional_test_field: Optional[int] = None


class TestSchema(Schema):
    ref_field = fields.Int()
    test_field = ResolvableField(int, required=True, allow_none=False)
    optional_ref_field = ResolvableField(int, required=False, allow_none=True)
    optional_test_field = ResolvableField(int, required=False, allow_none=True)

    @post_load
    def make(self, data, **kwargs) -> TestResult:
        return TestResult(**data)


class NestedTestResult(NamedTuple):
    root_field: int
    nested: TestResult


class NestedTestSchema(Schema):
    root_field = fields.Int()
    nested = fields.Nested(TestSchema)

    @post_load
    def make(self, data, **kwargs) -> NestedTestResult:
        return NestedTestResult(**data)


class TestCommon(TestCase):
    def test_resolvable_field(self):
        # given
        input = {
            "ref_field": 42,
            "test_field": "{ref_field}"
        }
        target = TestSchema()
        # when
        result = target.load(input)
        # then
        self.assertEqual(result.ref_field, 42)
        self.assertEqual(result.test_field, 42)

    def test_resolvable_field_ref_ref(self):
        # given
        input = {
            "ref_field": 42,
            "optional_ref_field": "{ref_field}",
            "test_field": "{optional_ref_field}"
        }
        target = TestSchema()
        # when
        result = target.load(input)
        # then
        self.assertEqual(result.test_field, 42)

    def test_resolvable_field_ref_ref_ref(self):
        # given
        input = {
            "ref_field": 42,
            "optional_ref_field": "{ref_field}",
            "test_field": "{optional_ref_field}",
            "optional_test_field": "{test_field}"
        }
        target = TestSchema()
        # when
        result = target.load(input)
        # then
        self.assertEqual(result.optional_test_field, 42)

    def test_resolvable_field_not_required(self):
        # given
        input = {
            "ref_field": 42,
            "test_field": 0,
        }
        target = TestSchema()
        # when
        result = target.load(input)
        # then
        self.assertEqual(result.ref_field, 42)
        self.assertEqual(result.test_field, 0)

    def test_resolvable_field_none_value(self):
        # given
        input = {
            "ref_field": 42,
            "test_field": 0,
            "optional_test_field": None
        }
        target = TestSchema()
        # when
        result = target.load(input)
        # then
        self.assertEqual(result.optional_test_field, None)

    def test_resolvable_field_resolve_to_none(self):
        # given
        input = {
            "ref_field": 42,
            "test_field": 0,
            "optional_ref_field": None,
            "optional_test_field": "{optional_ref_field}"
        }
        target = TestSchema()
        # when
        result = target.load(input)
        # then
        self.assertEqual(result.optional_ref_field, None)
        self.assertEqual(result.optional_test_field, None)

    def test_resolvable_field_resolve_to_none_fail(self):
        # given
        input = {
            "ref_field": 42,
            "test_field": "{optional_ref_field}",
            "optional_ref_field": None,
            "optional_test_field": "{optional_ref_field}"
        }
        target = TestSchema()
        # when
        self.assertRaises(ValidationError, lambda: target.load(input))

    def test_nested_resolvable_schema(self):
        # given
        input = {
            "root_field": 42,
            "nested": {
                "ref_field": 43,
                "test_field": "{root_field}"
            }
        }
        target = NestedTestSchema()
        target.context = input
        # given
        result = target.load(input)
        # when
        self.assertEqual(result.nested.test_field, 42)

    def test_nested_resolvable_schema_ref_ref_ref(self):
        # given
        input = {
            "root_field": 42,
            "nested": {
                "ref_field": 43,
                "optional_ref_field": "{root_field}",
                "test_field": "{optional_ref_field}",
                "optional_test_field": "{test_field}"
            }
        }
        target = NestedTestSchema()
        target.context = input
        # given
        result = target.load(input)
        # when
        self.assertEqual(result.nested.test_field, 42)
        self.assertEqual(result.nested.optional_test_field, 42)
        self.assertEqual(result.nested.optional_ref_field, 42)


if __name__ == '__main__':
    unittest.main()
