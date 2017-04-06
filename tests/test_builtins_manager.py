import unittest

from builtins_manager import BuiltinsManager


class TestBuiltins(unittest.TestCase):
    def setUp(self):
        self.builtins = BuiltinsManager()

    def test_none(self):
        """Test the None type."""
        self.assertEqual(
            self.builtins.none().name(),
            "None"
        )

    def test_int(self):
        """Test the int type."""


if __name__ == "__main__":
    unittest.main()
