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

x4 = 1
def func6():
    x4 = 1.0
    def inner():
        nonlocal x4
        x4 = "str"
        return x4
    return x4

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
    return func16()
""")
        self.types = self.inferer.environment()

    def test_assignment(self):
        """Test variable assignment."""
        self.assertSetEqual(self.types["x"].evaluate(), {"int", "str"})
        self.assertEqual(self.types["z"], self.types["x"])

    def test_augmented_assignment(self):
        """Test augmented assignment."""
        print(self.types["y"].evaluate())
        self.assertSetEqual(self.types["y"].evaluate(),
                            {"int", "str", "float"})

    def test_dict_literal(self):
        """Test literal dictionary contents."""
        self.assertEqual(self.types["d"].evaluate(),
                         ("Any", "Any"))
        self.assertEqual(self.types["d2"].evaluate(),
                         ("int", "str"))
        self.assertEqual(self.types["d3"].evaluate(),
                         (frozenset({"int", "str"}),
                          frozenset({"int", "float", "str"})))
        self.assertSetEqual(self.types["d4"].evaluate(),
                         frozenset([
                             (
                                 frozenset({"int", "str"}),
                                 frozenset({"int", "float", "str"})
                             ),
                             "str"
                         ]))

    def test_container(self):
        """Test literal container (list, set, tuple) contents."""
        self.assertEqual(self.types["l"].evaluate(), ("Any", ))
        self.assertEqual(self.types["s"].evaluate(), (frozenset(["int", "float"]), ))
        self.assertEqual(self.types["t"].evaluate(), ("str", ))
        self.assertEqual(self.types["l2"].evaluate(),
                         (frozenset([("str", ), (frozenset(["int", "float"]), )]), ))
        self.assertEqual(self.types["s2"].evaluate(),
                         frozenset([("int", ), ("float", )]))

    def test_unary_op(self):
        """Test unary operations."""
        self.assertEqual(self.types["b"].evaluate(), "bool")
        self.assertEqual(self.types["c"].evaluate(), "int")
        self.assertEqual(self.types["e"].evaluate(), "int")
        self.assertSetEqual(self.types["f"].evaluate(), {"int", "float"})

    def test_bin_op(self):
        """Test binary operation."""
        self.assertSetEqual(self.types["a"].evaluate(),
                            frozenset([(frozenset(["int", "float"]), ), "float"]))

    def test_function_return(self):
        """Test function return types."""
        self.assertEqual(self.types["func"].return_type.evaluate(), "None")
        self.assertEqual(self.types["func2"].return_type.evaluate(), "int")
        self.assertEqual(self.types["func3"].return_type, self.types["x2"])
        self.assertEqual(self.types["func4"].return_type.evaluate(), "str")


    def test_function_body_env(self):
        """Test the function body environment."""
        self.assertEqual(self.types["func4"].body_env["x2"].evaluate(), "str")

    def test_global(self):
        """Test handling of global variables."""
        self.assertSetEqual(self.types["func5"].return_type.evaluate(),
                            {"int", "float"})
        self.assertSetEqual(self.types["func5"].body_env["x3"].evaluate(),
                            {"int", "float"})
        self.assertSetEqual(self.types["x3"].evaluate(),
                            {"int", "float"})

    def test_nonlocal(self):
        """Test handling of nonlocal variables."""
        self.assertSetEqual(self.types["func6"].return_type.evaluate(),
                            {"str", "float"})
        self.assertEqual(self.types["func6"].return_type,
                         self.types["func6"].body_env["inner"].return_type)

        # The nonlocal variable should remain untouched
        self.assertEqual(self.types["x4"].evaluate(), "int")

    def test_positional_args(self):
        """Test positional argument handling."""
        self.assertEqual(self.types["func7"].return_type.evaluate(), "None")
        self.assertEqual(self.types["func7"].body_env["arg1"].evaluate(), "Any")
        self.assertEqual(self.types["func8"].return_type.evaluate(), "Any")

    def test_keyword_args(self):
        """Test keyword arguments."""
        self.assertEqual(self.types["func9"].return_type.evaluate(), "int")
        self.assertEqual(self.types["func9"].body_env["kwarg1"].evaluate(), "int")
        self.assertSetEqual(self.types["func10"].return_type.evaluate(),
                            {"None", "str"})
        self.assertSetEqual(self.types["func10"].body_env["kwarg1"].evaluate(),
                            {"None", "str"})
        self.assertEqual(self.types["func11"].return_type.evaluate(), "Any")
        self.assertEqual(self.types["func14"].return_type.evaluate(), "Any")
        self.assertEqual(self.types["func15"].return_type.evaluate(), "int")

    def test_vararg(self):
        """Test variable positional arguments."""
        self.assertEqual(self.types["func12"].return_type.evaluate(),
                         ("Any", ))

    def test_variable_keyword_args(self):
        """Test variable keyword arguments."""
        self.assertEqual(self.types["func13"].return_type.evaluate(),
                         ("Any", "Any"))


if __name__ == "__main__":
    unittest.main()

