# -*- coding: utf-8 -*-

import unittest
from inference import Inferer


class TestInference(unittest.TestCase):
    def test_assignment(self):
        """Test variable assignment."""
        code = """
x = 2
y = x
        """
        env = Inferer().environment()
        env.parse_code(code)

        self.assertSetEqual(
            {t.name() for t in env.lookup_types("x")},
            {"int"}
        )
        self.assertSetEqual(
            {t.name() for t in env.lookup_types("y")},
            {"int"}
        )

    def test_multiple_assignment(self):
        """Test assignment of a variable holding multiple types."""
        code = """
x = 2
x = 1.0
        """
        env = Inferer().environment()
        env.parse_code(code)

        self.assertSetEqual(
            {t.name() for t in env.lookup_types("x")},
            {"int", "float"}
        )

    def test_variable_reassignment(self):
        """Test that reassignment of a variable from another variable does not affect the original."""
        code = """
x = 2
y = x
x = 1.0
        """
        env = Inferer().environment()
        env.parse_code(code)

        self.assertSetEqual(
            {t.name() for t in env.lookup_types("x")},
            {"int", "float"}
        )
        self.assertSetEqual(
            {t.name() for t in env.lookup_types("y")},
            {"int"}
        )

    def test_function_definition(self):
        """Test function definitions."""
        code = """
def func():
    return 2
        """
        env = Inferer().environment()
        env.parse_code(code)



if __name__ == "__main__":
    unittest.main()


