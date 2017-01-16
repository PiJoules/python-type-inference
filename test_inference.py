#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from inference import *


class TestInference(unittest.TestCase):
    def test_assignment(self):
        """Test variable assignment."""
        code = """
x = 2
        """
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.lookup("x"),
            {IntInst()}
        )

    def test_function_call(self):
        """Test function calls."""
        code = """
def func():
    return 2
x = func()
        """
        env = ModuleEnv()
        env.parse_code(code)

        # Stored value
        self.assertSetEqual(
            env.lookup("x"),
            {IntInst()}
        )

        # Return type
        self.assertSetEqual(
            first(env.lookup("func")).type().returns(),
            {IntInst()}
        )

    def test_function_arg_call(self):
        """Test that the arguments influence the return type."""
        code = """
def func(a):
    return a
x = func(2)
        """
        env = ModuleEnv()
        env.parse_code(code)

        # Stored value
        self.assertSetEqual(
            env.lookup("x"),
            {IntInst()}
        )

        # Return type
        self.assertSetEqual(
            first(env.lookup("func")).type().returns(),
            {IntInst()}
        )

        # Argument in function
        self.assertSetEqual(
            first(env.lookup("func")).type().env().lookup("a"),
            {IntInst()}
        )

    def test_function_recursion(self):
        """Assert correct types in recursive functions."""
        code = """
def fib(n):
    if n < 2:
        return n
    return fib(n-1) + fib(n-2)
x = fib(5)
        """
        env = ModuleEnv()
        env.parse_code(code)

        # Stored value
        self.assertSetEqual(
            env.lookup("x"),
            {IntInst()}
        )

        # Return type
        self.assertSetEqual(
            first(env.lookup("fib")).type().returns(),
            {IntInst()}
        )

        # Argument in function
        self.assertSetEqual(
            first(env.lookup("fib")).type().env().lookup("n"),
            {IntInst()}
        )

    def test_class_instantiation(self):
        """Test creation of a class."""
        code = """
class A:
    pass
x = A()
        """
        env = ModuleEnv()
        env.parse_code(code)

        # Stored value
        self.assertSetEqual(
            env.lookup("x"),
            {MockInstance("A")}
        )

    def test_class_attributes(self):
        """Test variables assigned in a class are attributes of the class."""
        code = """
class A:
    x = 2
    def func(self, a):
        return a
x = A()
y = A.x
z = A.func(x, 2)
        """
        env = ModuleEnv()
        env.parse_code(code)

        # Stored value
        print("x:", env.lookup("x"))
        self.assertSetEqual(
            env.lookup("x"),
            {MockInstance("A")}
        )
        self.assertSetEqual(
            env.lookup("y"),
            {IntInst()}
        )
        self.assertSetEqual(
            env.lookup("z"),
            {IntInst()}
        )

        # Class attributes
        self.assertSetEqual(
            first(env.lookup("A")).type().get_attr("x"),
            {IntInst()}
        )
        self.assertSetEqual(
            first(env.lookup("A")).type().get_attr("func"),
            {MockFunction("func")}
        )

    def test_instance_attrs(self):
        """Test instance methods with self attribute assignments."""
        code = """
class A:
    def __init__(self, a):
        self._a = a
    def func(self):
        return self._a
x = A(2)
y = x.func()
        """
        env = ModuleEnv()
        env.parse_code(code)

        # Stored value
        self.assertSetEqual(
            env.lookup("x"),
            {MockInstance("A")}
        )
        self.assertSetEqual(
            env.lookup("y"),
            {IntInst()}
        )

        # Instance attributes
        self.assertSetEqual(
            first(first(env.lookup("x")).type().get_attr("func")).type().returns(),
            {IntInst()}
        )
        self.assertSetEqual(
            first(first(env.lookup("x")).type().get_attr("__init__")).type().returns(),
            {NoneInst()}
        )
        self.assertSetEqual(
            first(env.lookup("x")).type().get_attr("_a"),
            {IntInst()}
        )

    def test_multiple_instances(self):
        """Test the attributes change with multiple instances."""
        code = """
class A:
    def __init__(self, a):
        self._a = a
    def func(self):
        return self._a
x = A(2)
y = x.func()
x = A(4.0)
y = x.func()
        """
        env = ModuleEnv()
        env.parse_code(code)

        # Stored value
        self.assertSetEqual(
            env.lookup("x"),
            {MockInstance("A")}
        )
        self.assertSetEqual(
            env.lookup("y"),
            {IntInst(), FloatInst()}
        )

        # Instance attributes
        self.assertSetEqual(
            first(first(env.lookup("x")).type().get_attr("func")).type().returns(),
            {IntInst(), FloatInst()}
        )
        self.assertSetEqual(
            first(first(env.lookup("x")).type().get_attr("__init__")).type().returns(),
            {NoneInst()}
        )
        self.assertSetEqual(
            first(env.lookup("x")).type().get_attr("_a"),
            {IntInst(), FloatInst()}
        )

    def test_multiple_assignment(self):
        """Test variables can hold mutiple types."""
        code = """
class A:
    pass
x = A(2)
x = 2

y = x
y = 3.0

x = 4j
        """
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.lookup("x"),
            {MockInstance("A"), IntInst(), ComplexInst()}
        )
        self.assertSetEqual(
            env.lookup("y"),
            {MockInstance("A"), IntInst(), FloatInst()}
        )



if __name__ == "__main__":
    unittest.main()

