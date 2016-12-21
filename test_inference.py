#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from utils import *
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

    def test_function(self):
        """Test function return types and environments."""
        self.assertEqual(self.types["func"]["return_type"].evaluate(), "None")
        self.assertEqual(self.types["func2"]["return_type"].evaluate(), "int")
        self.assertEqual(self.types["func3"]["return_type"], self.types["x2"])


if __name__ == "__main__":
    unittest.main()

