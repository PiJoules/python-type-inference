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
        #self.assertEqual(self.types["func18"].callable_return_type().type(), "Any")
        self.assertEqual(self.types["func19"].callable_return_type().type(), "int")


if __name__ == "__main__":
    unittest.main()

