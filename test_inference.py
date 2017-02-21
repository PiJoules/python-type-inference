import unittest

from inference import ModuleEnv
from pytype import *
from instance_type import InstanceType


def first(x):
    return next(iter(x))


class TestInference(unittest.TestCase):
    def test_assign(self):
        """
        Test variable assignment
        """
        code = """
x = 2
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {IntType()}
        )

    def test_free_function_call(self):
        """
        Test calls to free functions.
        """
        code = """
def func(a):
    return a + 2
x = func(5)
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {IntType()}
        )

        # Function
        func = first(env.lookup("func"))
        self.assertSetEqual(
            func.returns(),
            {IntType()}
        )

        # Function env
        self.assertSetEqual(
            func.env().exclusive_lookup("a"),
            {IntType()}
        )

    def test_function_recursion(self):
        """
        Test correct types in recursive functions.
        """
        code = """
def fib(n):
    if n < 2:
        return n
    return fib(n-1) + fib(n-2)
x = fib(5)
        """
        env = ModuleEnv()
        env.parse_code(code)

        # Stored var
        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {IntType()}
        )

        # Function env
        func = first(env.exclusive_lookup("fib"))
        self.assertSetEqual(
            func.env().exclusive_lookup("n"),
            {IntType()}
        )

        # Function return type
        self.assertSetEqual(
            func.returns(),
            {IntType()}
        )

        # fib() not in func env
        self.assertRaises(KeyError, func.env().exclusive_lookup, "fib")

        # fib() in module env
        self.assertSetEqual(
            func.env().lookup("fib"),
            env.exclusive_lookup("fib")
        )

    def test_instance_attributes(self):
        """
        Test attributes of instances function correctly.
        """
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

        # Stored vars
        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {InstanceType("A")}
        )
        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {IntType()}
        )

        # Class functions
        cls = first(env.exclusive_lookup("A"))
        init_func = first(cls.get_attr("__init__"))
        self.assertSetEqual(
            init_func.env().exclusive_lookup("a"),
            {IntType()}
        )
        self.assertSetEqual(
            init_func.env().exclusive_lookup("self"),
            {InstanceType("A")}
        )
        self.assertRaises(KeyError, cls.get_attr, "_a")

        # Instance attributes
        inst = first(env.exclusive_lookup("x"))
        self.assertSetEqual(
            inst.get_attr("_a"),
            {IntType()}
        )

    def test_keyword_args(self):
        code = """
def func(a=1):
    return a
x = func()
y = func("b")
        """
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.lookup("x"),
            {IntType()}
        )
        self.assertSetEqual(
            env.lookup("y"),
            {StrType(), IntType()}
        )

        func = first(env.exclusive_lookup("func"))
        self.assertSetEqual(
            func.env().exclusive_lookup("a"),
            {StrType(), IntType()}
        )

    def test_vararg(self):
        code = """
def func(*args):
    return args[0]
x = func(1, "a")
        """
        env = ModuleEnv()
        env.parse_code(code)



if __name__ == "__main__":
    unittest.main()
