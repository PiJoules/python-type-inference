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
"""))
        self.types = self.inferer.types()

    def test_assignment(self):
        self.assertSetEqual(self.types["x"].evaluate(), {"int", "str"})


if __name__ == "__main__":
    unittest.main()

