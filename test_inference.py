import unittest

from inference import ModuleEnv
from pytype import *
from instance_type import InstanceMock
from tuple_type import TupleType
from dict_type import DictType
from int_type import INT_CLASS
from str_type import STR_CLASS


class TestInference(unittest.TestCase):
    def first(self, container):
        self.assertEqual(len(container), 1)
        return next(iter(container))

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
            {INT_CLASS.instance()}
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
            {INT_CLASS.instance()}
        )

        # Function
        func = self.first(env.lookup("func"))
        self.assertSetEqual(
            func.returns(),
            {INT_CLASS.instance()}
        )

        # Function env
        self.assertSetEqual(
            func.env().exclusive_lookup("a"),
            {INT_CLASS.instance()}
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
            {INT_CLASS.instance()}
        )

        # Function env
        func = self.first(env.exclusive_lookup("fib"))
        self.assertSetEqual(
            func.env().exclusive_lookup("n"),
            {INT_CLASS.instance()}
        )

        # Function return type
        self.assertSetEqual(
            func.returns(),
            {INT_CLASS.instance()}
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
            {InstanceMock("A")}
        )
        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {INT_CLASS.instance()}
        )

        # Class functions
        cls = self.first(env.exclusive_lookup("A"))
        init_func = self.first(cls.get_attr("__init__"))
        self.assertSetEqual(
            init_func.env().exclusive_lookup("a"),
            {INT_CLASS.instance()}
        )
        self.assertSetEqual(
            init_func.env().exclusive_lookup("self"),
            {InstanceMock("A")}
        )
        self.assertRaises(KeyError, cls.get_attr, "_a")

        # Instance attributes
        inst = self.first(env.exclusive_lookup("x"))
        self.assertSetEqual(
            inst.get_attr("_a"),
            {INT_CLASS.instance()}
        )

    def test_keyword_args(self):
        """Test keyword arguments."""
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
            {INT_CLASS.instance()}
        )
        self.assertSetEqual(
            env.lookup("y"),
            {STR_CLASS.instance(), INT_CLASS.instance()}
        )

        func = self.first(env.exclusive_lookup("func"))
        self.assertSetEqual(
            func.env().exclusive_lookup("a"),
            {STR_CLASS.instance(), INT_CLASS.instance()}
        )

    def test_vararg(self):
        """Test variable positional args."""
        code = """
def func(*args):
    return args[0]
def func2(*args):
    return args
x = func(1, "a")
y = func2(1, "a")
        """
        env = ModuleEnv()
        env.parse_code(code)

        tup = {TupleType(init_contents=({INT_CLASS.instance()}, {STR_CLASS.instance()}))}

        # Stored vars
        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {INT_CLASS.instance(), STR_CLASS.instance()}
        )
        self.assertSetEqual(
            env.exclusive_lookup("y"),
            tup
        )

        # func
        func = self.first(env.exclusive_lookup("func"))
        self.assertSetEqual(
            func.env().exclusive_lookup("args"),
            tup
        )
        self.assertSetEqual(
            func.returns(),
            {INT_CLASS.instance(), STR_CLASS.instance()}
        )

        # func2
        func2 = self.first(env.exclusive_lookup("func2"))
        self.assertSetEqual(
            func2.env().exclusive_lookup("args"),
            tup
        )
        self.assertSetEqual(
            func2.returns(),
            tup
        )

    def test_kwonly_args(self):
        """Test keyword only arguments."""
        code = """
def func(*, a, b=1):
    return a + b
x = func(a=1)
y = func(a=2, b=2)
        """
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {INT_CLASS.instance()}
        )
        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {INT_CLASS.instance()}
        )

        func = self.first(env.exclusive_lookup("func"))
        self.assertSetEqual(
            func.env().exclusive_lookup("a"),
            {INT_CLASS.instance()}
        )
        self.assertSetEqual(
            func.env().exclusive_lookup("b"),
            {INT_CLASS.instance()}
        )

    def test_kwarg(self):
        """Test the **kwarg."""
        code = """
def func(**kwargs):
    return kwargs["a"]
def func2(**kwargs):
    return kwargs
x = func(a=1)
y = func(a="str")
a = func2(a=1)
b = func2(a="str")
        """
        env = ModuleEnv()
        env.parse_code(code)

        d_types ={
            DictType(
                key_types={STR_CLASS.instance()},
                value_types={INT_CLASS.instance()}
            ),
            DictType(
                key_types={STR_CLASS.instance()},
                value_types={STR_CLASS.instance()}
            )
        }

        # Stored values
        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {INT_CLASS.instance()}
        )
        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {INT_CLASS.instance(), STR_CLASS.instance()}
        )
        self.assertSetEqual(
            env.exclusive_lookup("a"),
            {DictType(
                key_types={STR_CLASS.instance()},
                value_types={INT_CLASS.instance()}
            )}
        )
        self.assertSetEqual(
            env.exclusive_lookup("b"),
            d_types
        )

        # func()
        func = self.first(env.exclusive_lookup("func"))
        self.assertSetEqual(
            func.env().exclusive_lookup("kwargs"),
            d_types
        )
        self.assertSetEqual(
            func.returns(),
            {INT_CLASS.instance(), STR_CLASS.instance()}
        )

        # func2()
        func2 = self.first(env.exclusive_lookup("func2"))
        self.assertSetEqual(
            func2.env().exclusive_lookup("kwargs"),
            d_types
        )
        self.assertSetEqual(
            func2.returns(),
            d_types
        )

    def test_multiple_instances(self):
        """
        Test that changes in different instances affect all instances.
        """
        code = """
class A:
    def __init__(self, a):
        self._a = a
    def func(self):
        return self._a
x = A(1)
y = A("1")
z = x
x.b = 2
        """
        env = ModuleEnv()
        env.parse_code(code)

        # Instance variables
        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {InstanceMock("A")}
        )
        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {InstanceMock("A")}
        )

        # Class functions
        cls = self.first(env.exclusive_lookup("A"))
        init_func = self.first(cls.get_attr("__init__"))
        self.assertSetEqual(
            init_func.env().exclusive_lookup("a"),
            {INT_CLASS.instance(), STR_CLASS.instance()}
        )
        self.assertSetEqual(
            init_func.env().exclusive_lookup("self"),
            {InstanceMock("A")}
        )
        self.assertRaises(KeyError, cls.get_attr, "_a")

        # Instance attributes
        x_inst = self.first(env.exclusive_lookup("x"))
        self.assertSetEqual(
            x_inst.get_attr("_a"),
            {INT_CLASS.instance(), STR_CLASS.instance()}
        )
        self.assertSetEqual(
            x_inst.get_attr("b"),
            {INT_CLASS.instance()}
        )
        y_inst = self.first(env.exclusive_lookup("y"))
        self.assertSetEqual(
            y_inst.get_attr("_a"),
            {INT_CLASS.instance(), STR_CLASS.instance()}
        )
        self.assertSetEqual(
            y_inst.get_attr("b"),
            {INT_CLASS.instance()}
        )
        z_inst = self.first(env.exclusive_lookup("z"))
        self.assertSetEqual(
            z_inst.get_attr("_a"),
            {INT_CLASS.instance(), STR_CLASS.instance()}
        )
        self.assertSetEqual(
            z_inst.get_attr("b"),
            {INT_CLASS.instance()}
        )



if __name__ == "__main__":
    unittest.main()
