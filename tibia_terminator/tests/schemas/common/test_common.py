#!/usr/bin/env python3.8

import unittest

from unittest import TestCase
from typing import NamedTuple, Optional, List
from marshmallow import fields, ValidationError
from tibia_terminator.schemas.common import (ResolvableField, FactorySchema)


class TestResult(NamedTuple):
    ref_field: int
    test_field: int
    optional_ref_field: Optional[int] = None
    optional_test_field: Optional[int] = None


class TestSchema(FactorySchema[TestResult]):
    ctor = TestResult
    ref_field = fields.Int()
    test_field = ResolvableField(int, required=True, allow_none=False)
    optional_ref_field = ResolvableField(int, required=False, allow_none=True)
    optional_test_field = ResolvableField(int, required=False, allow_none=True)


class NestedTestResult(NamedTuple):
    root_field: int
    nested: TestResult


class NestedTestSchema(FactorySchema[NestedTestResult]):
    ctor = NestedTestResult
    root_field = fields.Int()
    nested = fields.Nested(TestSchema)


class NestedListTestResult(NamedTuple):
    root_field: int
    nested_list: List[TestResult]


class NestedListTestSchema(FactorySchema[NestedListTestResult]):
    ctor = NestedListTestResult
    root_field = fields.Int()
    nested_list = fields.List(fields.Nested(TestSchema))


class TestCommon(TestCase):
    def test_resolvable_field(self):
        # given
        input = {"ref_field": 42, "test_field": "{ref_field}"}
        target = TestSchema()
        # when
        result = target.load(input)
        # then
        self.assertEqual(result.ref_field, 42)
        self.assertEqual(result.test_field, 42)

    def test_resolvable_field_expr(self):
        # given
        input = {"ref_field": 42, "test_field": "{ref_field+1}"}
        target = TestSchema()
        # when
        result = target.load(input)
        # then
        self.assertEqual(result.ref_field, 42)
        self.assertEqual(result.test_field, 43)

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
        input = {"ref_field": 42, "test_field": 0, "optional_test_field": None}
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
        # given
        result = target.load(input)
        # when
        self.assertEqual(result.nested.test_field, 42)
        self.assertEqual(result.nested.optional_test_field, 42)
        self.assertEqual(result.nested.optional_ref_field, 42)

    def test_nested_list_resolvable_schema_ref_ref_ref(self):
        # given
        input = {
            "root_field":
            42,
            "nested_list": [{
                "ref_field": 43,
                "optional_ref_field": "{ref_field}",
                "test_field": "{optional_ref_field}",
                "optional_test_field": "{test_field}"
            }, {
                "ref_field": 44,
                "optional_ref_field": "{root_field}",
                "test_field": "{optional_ref_field}",
                "optional_test_field": "{test_field}"
            }]
        }
        target = NestedListTestSchema()
        # given
        result = target.load(input)
        # when
        self.assertEqual(result.nested_list[0].ref_field, 43)
        self.assertEqual(result.nested_list[0].optional_ref_field, 43)
        self.assertEqual(result.nested_list[0].test_field, 43)
        self.assertEqual(result.nested_list[0].optional_test_field, 43)
        self.assertEqual(result.nested_list[1].ref_field, 44)
        self.assertEqual(result.nested_list[1].optional_test_field, 42)
        self.assertEqual(result.nested_list[1].test_field, 42)
        self.assertEqual(result.nested_list[1].optional_ref_field, 42)


if __name__ == '__main__':
    unittest.main()
