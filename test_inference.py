#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from inference import *


class TestInference(unittest.TestCase):
    def test_assignment(self):
        """Test variable assignment."""
        code = """
x = 2
        """
        env = Environment()
        env.parse_code(code)

        self.assertSetEqual(
            env.lookup("x"),
            {IntInst()}
        )

    def test_function_call(self):
        """Test function calls."""
        code = """
def func():
    return 2
x = func()
        """
        env = Environment()
        env.parse_code(code)

        # Stored value
        self.assertSetEqual(
            env.lookup("x"),
            {IntInst()}
        )

        # Return type
        self.assertSetEqual(
            first(env.lookup("func")).returns(),
            {IntInst()}
        )


if __name__ == "__main__":
    unittest.main()

