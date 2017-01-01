# -*- coding: utf-8 -*-

import unittest
import json
from inference import *


class TestInference(unittest.TestCase):
    def test_assignment(self):
        """Test variable assignment"""
        code = """
x = 2
        """
        env = Environment()
        env.parse_code(code)

        self.assertSetEqual(
            env.lookup("x"),
            {IntObject()}
        )

    def test_multiple_assignment(self):
        """Test multiple assignment of types to the same variable."""
        code = """
x = 2
x = 1.0
        """
        env = Environment()
        env.parse_code(code)

        self.assertSetEqual(
            env.lookup("x"),
            {IntObject(), FloatObject()}
        )

    def test_reassignment(self):
        """Test that assigning a type to another variable does not affect the first."""
        code = """
x = 2
y = x
x = 1.0
        """
        env = Environment()
        env.parse_code(code)

        self.assertSetEqual(
            env.lookup("x"),
            {IntObject(), FloatObject()}
        )

        self.assertSetEqual(
            env.lookup("y"),
            {IntObject()}
        )

    def test_function_definition(self):
        """Test function definitions."""
        code = """
def func():
    return 2

x = func()
        """
        env = Environment()
        env.parse_code(code)

        self.assertSetEqual(
            simple(env.lookup("func")).return_type(),
            {IntObject()}
        )
        self.assertEqual(
            env.lookup("x"),
            {IntObject()}
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
        env = Environment(code)
        env.parse_code(code)

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
        env = Environment(code)
        env.parse_code(code)

        # Argument
        self.assertSetEqual(
            simple(env.lookup("func")).environment().lookup("arg"),
            {IntObject()}
        )
        # Return type
        self.assertSetEqual(
            simple(env.lookup("func")).return_type(),
            {IntObject()}
        )

    def test_func_def_varargs(self):
        """Test function definition with variable arguments (*args)."""
        code = """
def func(*args):
    return args
        """
        env = Environment()
        env.parse_code(code)

        # Argument
        self.assertSetEqual(
            simple(env.lookup("func")).environment().lookup("args"),
            {ContainerObject()}
        )
        # Return type
        self.assertSetEqual(
            simple(env.lookup("func")).return_type(),
            {ContainerObject()}
        )
        # Tuple contents
        self.assertEqual(
            simple(simple(env.lookup("func")).environment().lookup("args"))
            .content_types(),
            {AnyObject()}
        )

    def test_func_def_kwargs(self):
        """Test function definition with **kwargs."""
        code = """
def func(**kwargs):
    return kwargs
        """
        env = Environment()
        env.parse_code(code)

        # Arguments
        self.assertSetEqual(
            simple(env.lookup("func")).environment().lookup("kwargs"),
            {DictObject()}
        )
        # Return type
        self.assertSetEqual(
            simple(env.lookup("func")).return_type(),
            {DictObject()}
        )
        # Dict contents
        self.assertSetEqual(
            simple(simple(env.lookup("func")).environment().lookup("kwargs"))
            .value_types(),
            {AnyObject()}
        )
        self.assertSetEqual(
            simple(simple(env.lookup("func")).environment().lookup("kwargs"))
            .key_types(),
            {AnyObject()}
        )

    def test_func_call_positional(self):
        """Test new argument types by function call arguments."""
        code = """
def func(arg):
    return arg

x = func(2)
        """
        env = Environment()
        env.parse_code(code)

        # Saved value
        self.assertSetEqual(
            env.lookup("x"),
            {IntObject()}
        )
        # Argument
        self.assertSetEqual(
            simple(env.lookup("func")).environment().lookup("arg"),
            {IntObject()}
        )
        # Return value
        self.assertSetEqual(
            simple(env.lookup("func")).return_type(),
            {IntObject()}
        )

    def test_func_call_keyword(self):
        """Test new argument types by function call arguments with keyword arguments."""
        code = """
def func(arg=1.0):
    return arg

x = func(arg=2)
        """
        env = Environment()
        env.parse_code(code)

        # Saved value
        self.assertSetEqual(
            env.lookup("x"),
            {IntObject(), FloatObject()}
        )
        # Argument
        self.assertSetEqual(
            simple(env.lookup("func")).environment().lookup("arg"),
            {IntObject(), FloatObject()}
        )
        # Return types
        self.assertSetEqual(
            simple(env.lookup("func")).return_type(),
            {IntObject(), FloatObject()}
        )

    def test_no_specified_return_type(self):
        """A function with no explicit return statement should return None."""
        code = """
def func(arg=1.0):
    pass

x = func()
        """
        env = Environment()
        env.parse_code(code)

        # Saved value
        self.assertSetEqual(
            env.lookup("x"),
            {NoneObject()}
        )
        # Return type
        self.assertSetEqual(
            simple(env.lookup("func")).return_type(),
            {NoneObject()}
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
func()
        """
        env = Environment()
        env.parse_code(code)

        # Outer
        self.assertSetEqual(
            env.lookup("x"),
            {IntObject(), StringObject()}
        )
        # Inner
        self.assertSetEqual(
            simple(env.lookup("func")).environment().lookup("x"),
            {FloatObject()}
        )

    def test_uncalled_functions(self):
        """Test that an uncalled function does not have its env evaluated."""
        code = """
def func():
    x = 1.0
        """
        env = Environment()
        env.parse_code(code)

        self.assertDictEqual(
            simple(env.lookup("func")).environment().variables(),
            {}
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
        env = Environment()
        env.parse_code(code)

        # Saved type
        self.assertSetEqual(
            env.lookup("x", ignore_parent=True),
            {IntObject()}
        )
        # Outer
        self.assertSetEqual(
            simple(env.lookup("func", ignore_parent=True)).return_type(),
            {IntObject()}
        )
        # Inner (2nd)
        self.assertSetEqual(
            simple(simple(env.lookup("func", ignore_parent=True))
            .environment().lookup("func", ignore_parent=True)).return_type(),
            {IntObject()}
        )
        # Inner most
        self.assertSetEqual(
            simple(simple(simple(env.lookup("func", ignore_parent=True))
            .environment().lookup("func", ignore_parent=True)).environment()
            .lookup("func", ignore_parent=True)).return_type(),
            {IntObject()}
        )

    def test_class_definition(self):
        """Test class definition."""
        code = """
class A:
    x = 2

x = A.x
        """
        env = Environment()
        env.parse_code(code)

        # Saved value
        self.assertSetEqual(
            env.lookup("x"),
            {IntObject()}
        )

        # Attribute
        self.assertSetEqual(
            simple(env.lookup("A")).get_attr("x"),
            {IntObject()}
        )

        self.assertSetEqual(
            env.types()[ClassObjectMock("A")]["x"],
            {IntObject()}
        )

    def test_class_method_definition(self):
        """Test function defitnitions inside a class."""
        code = """
class A:
    def func(arg):
        return arg

x = A.func(2)
        """
        env = Environment()
        env.parse_code(code)

        # Saved value
        self.assertSetEqual(
            env.lookup("x"),
            {IntObject()}
        )

        # Return type
        self.assertSetEqual(
            simple(simple(env.lookup("A")).get_attr("func"))
            .return_type(),
            {IntObject()}
        )

        self.assertSetEqual(
            simple(env.types()[ClassObjectMock("A")]["func"]).environment().lookup("arg"),
            {IntObject()}
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
        env = Environment()
        env.parse_code(code)

        self.assertSetEqual(
            env.lookup("x"),
            {IntObject()}
        )
        self.assertSetEqual(
            env.lookup("y"),
            {IntObject()}
        )
        self.assertSetEqual(
            env.types()[IntObject()]["a"],
            {IntObject(), FloatObject()}
        )

    def test_attribute_reassignment(self):
        """Test attribute reassingment on a variable."""
        code = """
class A:
    def func(arg):
        return arg

A.func = 2
        """
        env = Environment()
        env.parse_code(code)

        self.assertSetEqual(
            env.types()[ClassObjectMock("A")]["func"],
            {FunctionObjectMock("func"), IntObject()}
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
z = y.a()
        """
        env = Environment()
        env.parse_code(code)

        # Stored value
        self.assertSetEqual(
            env.lookup("x"),
            {InstanceObjectMock("A")}
        )
        self.assertSetEqual(
            env.lookup("y"),
            {InstanceObjectMock("A")}
        )
        self.assertSetEqual(
            env.lookup("z"),
            {StringObject()}
        )

        self.assertSetEqual(
            env.types()[InstanceObjectMock("A")]["_a"],
            {StringObject()}
        )

        # Attributes of x
        self.assertSetEqual(
            simple(simple(env.lookup("x")).get_attr("a")).return_type(),
            {StringObject()}
        )
        self.assertSetEqual(
            simple(env.lookup("x")).get_attr("_a"),
            {StringObject()}
        )
        self.assertSetEqual(
            simple(simple(env.lookup("x")).get_attr("func")).return_type(),
            {InstanceObjectMock("A")}
        )

        # Attributes of y
        self.assertSetEqual(
            simple(simple(env.lookup("y")).get_attr("a")).return_type(),
            {StringObject()}
        )
        self.assertSetEqual(
            simple(env.lookup("y")).get_attr("_a"),
            {StringObject()}
        )
        self.assertSetEqual(
            simple(simple(env.lookup("y")).get_attr("func")).return_type(),
            {InstanceObjectMock("A")}
        )

    def test_method_access_to_class(self):
        """Test that methods have access to their classes."""
        code = """
class A:
    def func(self):
        pass
        """
        env = Environment()
        env.parse_code(code)

        # Just show the return type is the class itself
        self.assertSetEqual(
            simple(simple(simple(env.lookup("A")).get_attr("func")).environment()
            .lookup("A")).return_type(),
            {InstanceObjectMock("A")}
        )

    def test_function_access_to_self(self):
        """Test that a function has access to itself in its environment."""
        code = """
def func():
    return 2
        """
        env = Environment()
        env.parse_code(code)

        self.assertSetEqual(
            simple(env.lookup("func")).environment().lookup("func"),
            {FunctionObjectMock("func")}
        )

    def test_uninferable_recursive_call(self):
        """Test functional recursive calls that cannot be evaluated to anything."""
        code = """
def func():
    return func()

x = func()
        """
        env = Environment()
        env.parse_code(code)

        # Saved value
        self.assertSetEqual(
            env.lookup("x"),
            set()
        )

    def test_inferable_recursive_call(self):
        """Test that recursive calls that return another value return that value."""
        code = """
def fib(n):
    if n < 2:
        return n
    return fib(n-1) + fib(n-2)

x = fib(5)
        """
        env = Environment()
        env.parse_code(code)

        # Saved value
        self.assertSetEqual(
            env.lookup("x"),
            {IntObject()}
        )

    def test_mutual_recursion(self):
        """Test mutual recursion among multiple functions."""
        code = """
def func():
    return func2()
def func2():
    return func3()
def func3():
    return func()
x = func()
        """
        env = Environment()
        env.parse_code(code)

        self.assertEqual(
            env.lookup("x"),
            set()
        )


if __name__ == "__main__":
    unittest.main()

