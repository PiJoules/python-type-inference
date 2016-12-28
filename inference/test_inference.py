#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import json
from inference import Environment, simple


class TestTypeInference(unittest.TestCase):
    def test_assignment(self):
        """Test variable assignment."""
        code = """
x = 2
        """
        env = Environment.from_code(code)

        self.assertSetEqual(env.lookup_values("x"), {"int"})

    def test_multiple_assignment(self):
        """Test assignment of multiple types to the same variable."""
        code = """
x = 2
x = "string"
x = 3
        """
        env = Environment.from_code(code)

        self.assertSetEqual(env.lookup_values("x"), {"int", "str"})

    def test_function_definition(self):
        """Test function definitions."""
        code = """
def func():
    return 2
        """
        env = Environment.from_code(code)

        self.assertEqual(
            simple(simple(env.lookup("func")).return_type()).value(),
            "int"
        )

    def test_func_def_default_args(self):
        """
        Test function definition with an argument and the function is not
        called. There is no parseable type in this case.
        """
        code = """
def func(arg):
    return arg
        """
        env = Environment.from_code(code)

        # Argument
        self.assertEqual(
            simple(env.lookup("func")).environment().lookup("arg"),
            set()
        )
        # Return type
        self.assertEqual(
            simple(env.lookup("func")).return_type(),
            set()
        )

    def test_func_def_keyword_args(self):
        """Test function definition with default keyword arguments."""
        code = """
def func(arg=2):
    return arg
        """
        env = Environment.from_code(code)

        # Argument
        self.assertEqual(
            simple(simple(env.lookup("func")).environment().lookup("arg")).value(),
            "int"
        )
        # Return type
        self.assertEqual(
            simple(simple(env.lookup("func")).return_type()).value(),
            "int"
        )

    def test_func_def_varargs(self):
        """Test function definition with variable arguments (*args)."""
        code = """
def func(*args):
    return args
        """
        env = Environment.from_code(code)

        # Argument
        self.assertEqual(
            simple(simple(env.lookup("func")).environment().lookup("args")).value(),
            "tuple"
        )
        # Return type
        self.assertEqual(
            simple(simple(env.lookup("func")).return_type()).value(),
            "tuple"
        )
        # Tuple contents
        self.assertEqual(
            simple(simple(simple(env.lookup("func")).environment().lookup("args"))
            .contents()).value(),
            "Any"
        )

    def test_func_def_kwargs(self):
        """Test function definition with **kwargs."""
        code = """
def func(**kwargs):
    return kwargs
        """
        env = Environment.from_code(code)

        # Arguments
        self.assertEqual(
            simple(simple(env.lookup("func")).environment().lookup("kwargs")).value(),
            "dict"
        )
        # Return type
        self.assertEqual(
            simple(simple(env.lookup("func")).return_type()).value(),
            "dict"
        )
        # Dict contents
        self.assertEqual(
            simple(simple(simple(env.lookup("func")).environment().lookup("kwargs"))
            .value_contents()).value(),
            "Any"
        )
        self.assertEqual(
            simple(simple(simple(env.lookup("func")).environment().lookup("kwargs"))
            .key_contents()).value(),
            "Any"
        )

    def test_func_call_positional(self):
        """Test new argument types by function call arguments."""
        code = """
def func(arg):
    return arg

x = func(2)
        """
        env = Environment.from_code(code)

        # Saved value
        self.assertEqual(
            simple(env.lookup("x")).value(),
            "int"
        )
        # Argument
        self.assertEqual(
            simple(simple(env.lookup("func")).environment().lookup("arg")).value(),
            "int"
        )
        # Return value
        self.assertEqual(
            simple(simple(env.lookup("func")).return_type()).value(),
            "int"
        )

    def test_func_call_keyword(self):
        """Test new argument types by function call arguments with keyword arguments."""
        code = """
def func(arg=1.0):
    return arg

x = func(arg=2)
        """
        env = Environment.from_code(code)

        # Saved value
        self.assertSetEqual(
            env.lookup_values("x"),
            {"int", "float"}
        )
        # Argument
        self.assertSetEqual(
            simple(env.lookup("func")).environment().lookup_values("arg"),
            {"int", "float"}
        )
        # Return types
        self.assertSetEqual(
            {t.value() for t in simple(env.lookup("func")).return_type()},
            {"int", "float"}
        )

    def test_no_specified_return_type(self):
        """A function with no explicit return statement should return None."""
        code = """
def func(arg=1.0):
    pass

x = func()
        """
        env = Environment.from_code(code)

        # Saved value
        self.assertEqual(
            simple(env.lookup("x")).value(),
            "None"
        )
        # Return type
        self.assertEqual(
            simple(simple(env.lookup("func")).return_type()).value(),
            "None"
        )

    def test_function_variable_redefinition(self):
        """
        Test that variables with same name as a variable in an outer type
        contains different types if overwritten.
        """
        code = """
x = 1

def func():
    x = 1.0

x = "str"
        """
        env = Environment.from_code(code)

        # Outer
        self.assertSetEqual(
            env.lookup_values("x"),
            {"int", "str"}
        )
        # Inner
        self.assertEqual(
            simple(simple(env.lookup("func")).environment().lookup("x")).value(),
            "float"
        )

    def test_nested_functions(self):
        """Test nested function calls."""
        code = """
def func():
    def func():
        def func():
            return 2
        return func()
    return func()
x = func()
        """
        env = Environment.from_code(code)

        # Saved type
        self.assertEqual(
            simple(env.lookup("x", ignore_parent=True)).value(),
            "int"
        )
        # Outer
        self.assertEqual(
            simple(simple(env.lookup("func", ignore_parent=True)).return_type()).value(),
            "int"
        )
        # Inner (2nd)
        self.assertEqual(
            simple(simple(simple(env.lookup("func", ignore_parent=True))
            .environment().lookup("func", ignore_parent=True)).return_type()).value(),
            "int"
        )
        # Inner most
        self.assertEqual(
            simple(simple(simple(simple(env.lookup("func", ignore_parent=True))
            .environment().lookup("func", ignore_parent=True)).environment()
            .lookup("func", ignore_parent=True)).return_type()).value(),
            "int"
        )

    def test_class_definition(self):
        """Test class definition."""
        code = """
class A:
    x = 2

x = A.x
        """
        env = Environment.from_code(code)

        # Saved value
        self.assertEqual(
            simple(env.lookup("x")).value(),
            "int"
        )

        # Attribute
        self.assertEqual(
            simple(simple(env.lookup("A")).get_attr("x")).value(),
            "int"
        )

    def test_class_method_definition(self):
        """Test function defitnitions inside a class."""
        code = """
class A:
    def func(arg):
        return arg

x = A.func(2)
        """
        env = Environment.from_code(code)

        # Saved value
        self.assertEqual(
            simple(env.lookup("x")).value(),
            "int"
        )

        # Return type
        self.assertEqual(
            simple(simple(simple(env.lookup("A")).get_attr("func"))
            .return_type()).value(),
            "int"
        )

    def test_variable_reassignment(self):
        """
        Test that a change to a variable assigned from another variable
        does not affect the first variable types.
        """
        code = """
x = 1
y = x
x = 1.0
y = 2j
        """
        env = Environment.from_code(code)

        self.assertSetEqual(
            env.lookup_values("x"),
            {"int", "float"}
        )
        self.assertSetEqual(
            env.lookup_values("y"),
            {"int", "complex"}
        )

    def test_variable_attribute_assignment(self):
        """
        Test that copied types through variable assignment from another
        variable still affect the same types when a new attribute is added.
        """
        code = """
x = 1
x.a = 5
y = x
y.a = 5.0
        """
        env = Environment.from_code(code)

        self.assertEqual(
            simple(env.lookup("x")).value(),
            "int"
        )
        self.assertEqual(
            simple(env.lookup("y")).value(),
            "int"
        )
        self.assertSetEqual(
            {t.value() for t in simple(env.lookup("x")).get_attr("a")},
            {"int", "float"}
        )
        self.assertSetEqual(
            {t.value() for t in simple(env.lookup("y")).get_attr("a")},
            {"int", "float"}
        )

    def test_attribute_reassignment(self):
        """Tets attribute reassingment on a variable."""
        code = """
class A:
    def func(arg):
        return arg

A.func = 2
        """
        env = Environment.from_code(code)

        self.assertSetEqual(
            {t.value() for t in simple(simple(env.lookup("A")).get_attr("func"))},
            {"function", "int"}
        )

    def test_instance_creation(self):
        """Test that all attributes of an instance are created on creation."""
        code = """
class A:
    def a(self):
        return self._a
    def func(self):
        return self
    def __init__(self, arg):
        self._a = arg

x = A("string")
y = x.func()
        """
        env = Environment.from_code(code)

        # Stored value
        self.assertEqual(
            simple(env.lookup("x")).value(),
            "A"
        )
        self.assertEqual(
            simple(env.lookup("y")).value(),
            "A"
        )

        # Attributes of x
        self.assertEqual(
            simple(simple(simple(env.lookup("x")).get_attr("a")).return_type())
            .value(),
            "str"
        )
        self.assertEqual(
            simple(simple(env.lookup("x")).get_attr("_a")).value(),
            "str"
        )
        self.assertEqual(
            simple(simple(simple(env.lookup("x")).get_attr("func")).return_type())
            .value(),
            "A"
        )

        # Attributes of y
        self.assertEqual(
            simple(simple(simple(env.lookup("y")).get_attr("a")).return_type())
            .value(),
            "str"
        )
        self.assertEqual(
            simple(simple(env.lookup("y")).get_attr("_a")).value(),
            "str"
        )
        self.assertEqual(
            simple(simple(simple(env.lookup("y")).get_attr("func")).return_type())
            .value(),
            "A"
        )


if __name__ == "__main__":
    unittest.main()


