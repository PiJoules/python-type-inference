#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import inference


class TestTypeInference(unittest.TestCase):
    def test_assignment(self):
        """Test variable assignment."""
        code = """
x = 2
        """
        env = inference.Environment.from_code(code)

        self.assertSetEqual(env.lookup_values("x"), {"int"})

    def test_multiple_assignment(self):
        """Test assignment of multiple types to the same variable."""
        code = """
x = 2
x = "string"
x = 3
        """
        env = inference.Environment.from_code(code)

        self.assertSetEqual(env.lookup_values("x"), {"int", "str"})



if __name__ == "__main__":
    unittest.main()


