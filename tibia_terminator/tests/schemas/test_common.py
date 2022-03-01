#!/usr/bin/env python3.8

import unittest

from unittest import TestCase
from typing import NamedTuple, Optional, List
from marshmallow import fields, ValidationError
from tibia_terminator.schemas.common import ResolvableField, FactorySchema


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


class MultiVarTestResult(NamedTuple):
    ref_field_1: int
    ref_field_2: int
    test_field: int


class MultiVarTestSchema(FactorySchema[MultiVarTestResult]):
    ctor = MultiVarTestResult
    ref_field_1 = fields.Int()
    ref_field_2 = fields.Int()
    test_field = ResolvableField(int, required=True, allow_none=False)


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

    def test_resolvable_field_dangerous_not_allowed(self):
        # given
        for builtin in [
            "eval",
            "exit",
            "compile",
            "__import__",
            "__loader__",
            "__build_class__",
            "__package_",
            "__spec__",
            "setattr",
            "locals",
            "memoryview",
            "quit",
            "exec",
            "exit",
            "_",
        ]:
            input = {"ref_field": 42, "test_field": f"{{{builtin}(ref_field)}}"}
            target = TestSchema()
            # when
            with self.assertRaises(NameError):
                target.load(input)

    def test_resolvable_field_with_math(self):
        # given
        input = {"ref_field": 42, "test_field": "{ref_field - 10}"}
        target = TestSchema()
        # when
        result = target.load(input)
        # then
        self.assertEqual(result.ref_field, 42)
        self.assertEqual(result.test_field, 32)

    def test_resolvable_field_with_math_multi_var(self):
        # given
        input = {
            "ref_field_1": 42,
            "ref_field_2": 12,
            "test_field": "{ref_field_1 - ref_field_2}",
        }
        target = MultiVarTestSchema()
        # when
        result = target.load(input)
        # then
        self.assertEqual(result.test_field, 30)

    def test_resolvable_field_with_math_fn_multi_var(self):
        # given
        input = {
            "ref_field_1": 42,
            "ref_field_2": 12,
            "test_field": "{max(ref_field_1 - ref_field_2, int(ref_field_1 * 0.9))}",
        }
        target = MultiVarTestSchema()
        # when
        result = target.load(input)
        # then
        self.assertEqual(result.test_field, 37)

    def test_resolvable_field_ref_ref(self):
        # given
        input = {
            "ref_field": 42,
            "optional_ref_field": "{ref_field}",
            "test_field": "{optional_ref_field}",
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
            "optional_test_field": "{test_field}",
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
            "optional_test_field": "{optional_ref_field}",
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
            "optional_test_field": "{optional_ref_field}",
        }
        target = TestSchema()
        # when
        self.assertRaises(ValidationError, lambda: target.load(input))

    def test_nested_resolvable_schema(self):
        # given
        input = {
            "root_field": 42,
            "nested": {"ref_field": 43, "test_field": "{root_field}"},
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
                "optional_test_field": "{test_field}",
            },
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
            "root_field": 42,
            "nested_list": [
                {
                    "ref_field": 43,
                    "optional_ref_field": "{ref_field}",
                    "test_field": "{optional_ref_field}",
                    "optional_test_field": "{test_field}",
                },
                {
                    "ref_field": 44,
                    "optional_ref_field": "{root_field}",
                    "test_field": "{optional_ref_field}",
                    "optional_test_field": "{test_field}",
                },
            ],
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

    def test_nested_list_resolvable_schema_multivar_math_fn(self):
        # given
        # ordering of the input dictionary affects results, so we rerun the
        # test 100 times.
        for _ in range(100):
            input = {
                "root_field": 42,
                "nested_list": [
                    {
                        "ref_field": 44,
                        "optional_ref_field": "{root_field}",
                        "test_field": "{optional_ref_field}",
                        "optional_test_field": "{max(root_field - ref_field, int(test_field * 0.8))}",
                    }
                ],
            }
            target = NestedListTestSchema()
            # given
            result = target.load(input)
            # when
            self.assertEqual(result.nested_list[0].optional_ref_field, 42)


if __name__ == "__main__":
    unittest.main()
