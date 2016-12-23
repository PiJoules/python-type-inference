#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from inference import TypeInferer


class TestTypeInference(unittest.TestCase):
    def setUp(self):
        self.inferer = TypeInferer.from_code(
"""
x = 2
x = "a"
x = 0

y = 0.1
y += x
z = x

d = {}
d2 = {2: "a"}
d3 = {x: y}
d4 = "a"
d4 = d3

l = []
s = {1, 1.0}
s = {2.0, 2}  # multiple assignment of same type for collection
t = ("str", )
l2 = [s, t]
s2 = {1}
s2 = {2.0}

a = s + 0.2
b = not a
c = ~b
e = +x
f = -y

def func():
    pass

def func2():
    return 2

x2 = 2
def func3():
    return x2

def func4():
    x2 = "some str"
    return x2

x3 = 5
def func5():
    global x3
    x3 = 1.0
    return x3

def func7(arg1):
    pass

def func8(arg1):
    return arg1

def func9(kwarg1=1):
    return kwarg1

def func10(kwarg1=None):
    kwarg1 = kwarg1 or "str"
    return kwarg1

def func11(arg1, kwarg1=None):
    return arg1 or kwarg1

def func12(a, b=1, *c, d, e=2, **f):
    return c

def func13(a, b=1, *c, d, e=2, **f):
    return f

def func14(a, b=1, *c, d, e=2, **f):
    return d

def func15(a, b=1, *c, d, e=2, **f):
    return e

def func16():
    return func9()

def func17():
    return func16() or "string"

def func18():
    return func18()

def func19():
    return func19() or 5

def func20():
    return func19() and func20()

def fib(n):
    return n if n < 2 else fib(n-1) + fib(n-2)

def func21(n):
    if n < 10:
        return 2
    else:
        return "a"

if x:
    n = 4
else:
    n = 1.0

def func22(n):
    while n < 10:
        return 2
    else:
        return "a"

while x:
    n2 = 4
else:
    n2 = 1.0

def func23(n):
    for i in range(4):
        return 2
    else:
        return "a"

for i in range(4):
    n3 = 4
else:
    n3 = 1.0

def func24():
    try:
        return 1
    except OSError as e:
        return 1.0
    except ValueError:
        return "1"
    except:
        return 2j
    else:
        return None
    finally:
        return -1.0

try:
    n4 = 1
except OSError as e:
    n4 = 1.0
except ValueError:
    n4 = "1"
except:
    n4 = 2j
else:
    n4 = None
finally:
    n4 = -1.0

def func25():
    with 2 as x:
        return x
    return 1.0

with 2.0 as n5:
    n5 = 1
""")
        self.types = self.inferer.environment()

    def test_assignment(self):
        """Test variable assignment."""
        self.assertSetEqual(self.types["x"].type(), {"int", "str"})
        self.assertEqual(self.types["z"], self.types["x"])

    def test_augmented_assignment(self):
        """Test augmented assignment."""
        self.assertSetEqual(self.types["y"].type(),
                            {"int", "str", "float"})

    def test_dict_literal(self):
        """Test literal dictionary contents."""
        self.assertEqual(self.types["d"].type(),
                         ("Any", "Any"))
        self.assertEqual(self.types["d2"].type(),
                         ("int", "str"))
        self.assertEqual(self.types["d3"].type(),
                         (frozenset({"int", "str"}),
                          frozenset({"int", "float", "str"})))
        self.assertSetEqual(self.types["d4"].type(),
                         frozenset([
                             (
                                 frozenset({"int", "str"}),
                                 frozenset({"int", "float", "str"})
                             ),
                             "str"
                         ]))

    def test_container(self):
        """Test literal container (list, set, tuple) contents."""
        self.assertEqual(self.types["l"].type(), ("Any", ))
        self.assertEqual(self.types["s"].type(), (frozenset(["int", "float"]), ))
        self.assertEqual(self.types["t"].type(), ("str", ))
        self.assertEqual(self.types["l2"].type(),
                         (frozenset([("str", ), (frozenset(["int", "float"]), )]), ))
        self.assertEqual(self.types["s2"].type(),
                         frozenset([("int", ), ("float", )]))

    def test_unary_op(self):
        """Test unary operations."""
        self.assertEqual(self.types["b"].type(), "bool")
        self.assertEqual(self.types["c"].type(), "int")
        self.assertEqual(self.types["e"].type(), "int")
        self.assertSetEqual(self.types["f"].type(), {"int", "float"})

    def test_bin_op(self):
        """Test binary operation."""
        self.assertSetEqual(self.types["a"].type(),
                            frozenset([(frozenset(["int", "float"]), ), "float"]))

    def test_function_return(self):
        """Test function return types."""
        self.assertEqual(self.types["func"].callable_return_type().type(), "None")
        self.assertEqual(self.types["func2"].callable_return_type().type(), "int")
        self.assertEqual(self.types["func3"].callable_return_type(), self.types["x2"])
        self.assertEqual(self.types["func4"].callable_return_type().type(), "str")


    def test_function_body_env(self):
        """Test the function body environment."""
        self.assertEqual(self.types["func4"].environment()["x2"].type(), "str")

    def test_global(self):
        """Test handling of global variables."""
        self.assertSetEqual(self.types["func5"].callable_return_type().type(),
                            {"int", "float"})
        self.assertSetEqual(self.types["func5"].environment()["x3"].type(),
                            {"int", "float"})
        self.assertSetEqual(self.types["x3"].type(),
                            {"int", "float"})

    def test_positional_args(self):
        """Test positional argument handling."""
        self.assertEqual(self.types["func7"].callable_return_type().type(), "None")
        self.assertEqual(self.types["func7"].environment()["arg1"].type(), "Any")
        self.assertEqual(self.types["func8"].callable_return_type().type(), "Any")

    def test_keyword_args(self):
        """Test keyword arguments."""
        self.assertEqual(self.types["func9"].callable_return_type().type(), "int")
        self.assertEqual(self.types["func9"].environment()["kwarg1"].type(), "int")
        self.assertSetEqual(self.types["func10"].callable_return_type().type(),
                            {"None", "str"})
        self.assertSetEqual(self.types["func10"].environment()["kwarg1"].type(),
                            {"None", "str"})
        self.assertEqual(self.types["func11"].callable_return_type().type(), "Any")
        self.assertEqual(self.types["func14"].callable_return_type().type(), "Any")
        self.assertEqual(self.types["func15"].callable_return_type().type(), "int")

    def test_vararg(self):
        """Test variable positional arguments."""
        self.assertEqual(self.types["func12"].callable_return_type().type(),
                         ("Any", ))

    def test_variable_keyword_args(self):
        """Test variable keyword arguments."""
        self.assertEqual(self.types["func13"].callable_return_type().type(),
                         ("Any", "Any"))

    def test_call(self):
        """Test function calls."""
        self.assertEqual(self.types["func16"].callable_return_type().type(), "int")
        self.assertSetEqual(self.types["func17"].callable_return_type().type(),
                            {"int", "str"})

    def test_recursive_call(self):
        """Test return types for recursive functions."""
        self.assertEqual(self.types["func18"].callable_return_type().type(), "Any")
        self.assertEqual(self.types["func19"].callable_return_type().type(), "int")
        self.assertEqual(self.types["func20"].callable_return_type().type(), "int")
        self.assertEqual(self.types["fib"].callable_return_type().type(), "Any")

    def test_if_statement(self):
        """Test if statement."""
        self.assertSetEqual(self.types["n"].type(), {"int", "float"})

    def test_func_if_statement(self):
        """Test if statements in a function."""
        self.assertSetEqual(self.types["func21"].callable_return_type().type(),
                            {"int", "str"})

    def test_while_statement(self):
        """Test while statement."""
        self.assertSetEqual(self.types["n2"].type(), {"int", "float"})

    def test_func_while_statement(self):
        """Test while statements in a function."""
        self.assertSetEqual(self.types["func22"].callable_return_type().type(),
                            {"int", "str"})

    def test_for_statement(self):
        """Test for statement."""
        self.assertSetEqual(self.types["n3"].type(), {"int", "float"})

    def test_func_for_statement(self):
        """Test for statements in a function."""
        self.assertSetEqual(self.types["func23"].callable_return_type().type(),
                            {"int", "str"})

    def test_try_statement(self):
        """Test try statement."""
        self.assertSetEqual(self.types["n4"].type(), {"int", "float", "complex", "str", "None"})

    def test_func_try_statement(self):
        """Test try statements in a function."""
        self.assertSetEqual(self.types["func24"].callable_return_type().type(),
                            {"int", "float", "complex", "str", "None"})

    def test_with_statement(self):
        """Test with statement."""
        self.assertSetEqual(self.types["n5"].type(), {"int", "float"})

    def test_func_with_statement(self):
        """Test with statements in a function."""
        self.assertSetEqual(self.types["func25"].callable_return_type().type(),
                            {"int", "float"})

    def test_func_assignment(self):
        """Test function assignment and calling."""
        env = TypeInferer.from_code("""
def func():
    return 2

x = func
y = func()
""").environment()
        self.assertEqual(env["func"].callable_return_type().type(), "int")
        self.assertEqual(env["x"].type(), "function")
        self.assertEqual(env["y"].type(), "int")

    def test_class_def(self):
        """Test class definitions."""
        env = TypeInferer.from_code("""
class A:
    pass
x = A()

y = x
y = 2
z = A
a = z()
""").environment()
        self.assertEqual(env["x"].type(), "A")

        # Multiple class definition
        self.assertSetEqual(env["y"].type(), {"A", "int"})

        # Class assignment and calling
        self.assertEqual(env["z"].type(), "type")
        self.assertEqual(env["a"].type(), "A")


if __name__ == "__main__":
    unittest.main()

