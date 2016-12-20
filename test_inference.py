#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from utils import *
from inference import TypeInferer


class TestTypeInference(unittest.TestCase):
    def setUp(self):
        self.inferer = TypeInferer(generate_ast(
"""
x = 2
x = "str"
x = 0

y = 0.1
y += x

x = 0.1
"""))
        self.types = self.inferer.types()

    def test_assignment(self):
        """Test variable assignment."""
        self.assertSetEqual(self.types["x"].evaluate(), {"int", "str", "float"})

    def test_augmented_assignment(self):
        """Test augmented assignment."""
        self.assertSetEqual(self.types["y"].evaluate(),
                            {"int", "str", "float"})


if __name__ == "__main__":
    unittest.main()

