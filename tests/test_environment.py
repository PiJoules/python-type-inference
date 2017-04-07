import unittest

from environment import ModuleEnv


class TestEnvironment(unittest.TestCase):
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
            {env.builtins().int()}
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
            {env.builtins().int()}
        )

        # Function
        func = self.first(env.lookup("func"))
        self.assertSetEqual(
            func.returns(),
            {env.builtins().int()}
        )

        # Function env
        self.assertSetEqual(
            func.env().exclusive_lookup("a"),
            {env.builtins().int()}
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
            {env.builtins().int()}
        )

        # Function env
        func = self.first(env.exclusive_lookup("fib"))
        self.assertSetEqual(
            func.env().exclusive_lookup("n"),
            {env.builtins().int()}
        )

        # Function return type
        self.assertSetEqual(
            func.returns(),
            {env.builtins().int()}
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

        a_inst = self.first(env.exclusive_lookup("A")).instance()

        # Stored vars
        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {a_inst}
        )
        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {env.builtins().int()}
        )

        # Class functions
        cls = self.first(env.exclusive_lookup("A"))
        init_func = self.first(cls.get_attr("__init__"))
        self.assertSetEqual(
            init_func.env().exclusive_lookup("a"),
            {env.builtins().int()}
        )
        self.assertSetEqual(
            init_func.env().exclusive_lookup("self"),
            {a_inst}
        )
        self.assertRaises(KeyError, cls.get_attr, "_a")

        # Instance attributes
        inst = self.first(env.exclusive_lookup("x"))
        self.assertSetEqual(
            inst.get_attr("_a"),
            {env.builtins().int()}
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
            {env.builtins().int()}
        )
        self.assertSetEqual(
            env.lookup("y"),
            {env.builtins().str(), env.builtins().int()}
        )

        func = self.first(env.exclusive_lookup("func"))
        self.assertSetEqual(
            func.env().exclusive_lookup("a"),
            {env.builtins().str(), env.builtins().int()}
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

        tup = {env.builtins().tuple_cls().instance(
            init_contents=({env.builtins().int()}, {env.builtins().str()}))}

        # Stored vars
        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {env.builtins().int(), env.builtins().str()}
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
            {env.builtins().int(), env.builtins().str()}
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
            {env.builtins().int()}
        )
        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {env.builtins().int()}
        )

        func = self.first(env.exclusive_lookup("func"))
        self.assertSetEqual(
            func.env().exclusive_lookup("a"),
            {env.builtins().int()}
        )
        self.assertSetEqual(
            func.env().exclusive_lookup("b"),
            {env.builtins().int()}
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
            env.builtins().dict_cls().instance(
                key_types={env.builtins().str()},
                value_types={env.builtins().int()}
            ),
            env.builtins().dict_cls().instance(
                key_types={env.builtins().str()},
                value_types={env.builtins().str()}
            )
        }

        # Stored values
        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {env.builtins().int()}
        )
        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {env.builtins().int(), env.builtins().str()}
        )
        self.assertSetEqual(
            env.exclusive_lookup("a"),
            {env.builtins().dict_cls().instance(
                key_types={env.builtins().str()},
                value_types={env.builtins().int()}
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
            {env.builtins().int(), env.builtins().str()}
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

        a_inst = self.first(env.exclusive_lookup("A")).instance()

        # Instance variables
        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {a_inst}
        )
        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {a_inst}
        )

        # Class functions
        cls = self.first(env.exclusive_lookup("A"))
        init_func = self.first(cls.get_attr("__init__"))
        self.assertSetEqual(
            init_func.env().exclusive_lookup("a"),
            {env.builtins().int(), env.builtins().str()}
        )
        self.assertSetEqual(
            init_func.env().exclusive_lookup("self"),
            {a_inst}
        )
        self.assertRaises(KeyError, cls.get_attr, "_a")

        # Instance attributes
        x_inst = self.first(env.exclusive_lookup("x"))
        self.assertSetEqual(
            x_inst.get_attr("_a"),
            {env.builtins().int(), env.builtins().str()}
        )
        self.assertSetEqual(
            x_inst.get_attr("b"),
            {env.builtins().int()}
        )
        y_inst = self.first(env.exclusive_lookup("y"))
        self.assertSetEqual(
            y_inst.get_attr("_a"),
            {env.builtins().int(), env.builtins().str()}
        )
        self.assertSetEqual(
            y_inst.get_attr("b"),
            {env.builtins().int()}
        )
        z_inst = self.first(env.exclusive_lookup("z"))
        self.assertSetEqual(
            z_inst.get_attr("_a"),
            {env.builtins().int(), env.builtins().str()}
        )
        self.assertSetEqual(
            z_inst.get_attr("b"),
            {env.builtins().int()}
        )



if __name__ == "__main__":
    unittest.main()
