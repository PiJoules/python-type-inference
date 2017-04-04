import unittest

from inference import ModuleEnv
from list_type import LIST_CLASS
from int_type import INT_CLASS
from str_type import STR_CLASS
from float_type import FLOAT_CLASS
from none_type import NONE_CLASS


class TestListType(unittest.TestCase):
    NON_EMPTY_LIST = LIST_CLASS.instance(
        init_contents=[{INT_CLASS.instance()}]
    )

    def test_empty_list_creation(self):
        """Test that I can make an emptylist."""
        code = """
x = []
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {LIST_CLASS.instance()}
        )
        self.assertNotEqual(
            env.exclusive_lookup("x"),
            {self.NON_EMPTY_LIST}
        )

    def test_list_initial_contents(self):
        """Test list creation with the elements in it."""
        code = """
x = [1, 3.0, "a"]
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {LIST_CLASS.instance(init_contents=[
                {STR_CLASS.instance()},
                {FLOAT_CLASS.instance()},
                {INT_CLASS.instance()},
            ])}
        )

    def test_list_equality(self):
        """Test various lists are equal."""
        # Multiple types of each contents
        self.assertSetEqual(
            {LIST_CLASS.instance(init_contents=[
                {STR_CLASS.instance()},
            ])},
            {LIST_CLASS.instance(init_contents=[
                {STR_CLASS.instance()},
                {STR_CLASS.instance()},
            ])}
        )

        # Order shouldn't matter
        self.assertSetEqual(
            {LIST_CLASS.instance(init_contents=[
                {STR_CLASS.instance()},
                {INT_CLASS.instance()},
            ])},
            {LIST_CLASS.instance(init_contents=[
                {INT_CLASS.instance()},
                {STR_CLASS.instance()},
            ])}
        )

        # Elements could be a combination of different types
        self.assertSetEqual(
            {LIST_CLASS.instance(init_contents=[
                {INT_CLASS.instance()},
                {STR_CLASS.instance()},
            ])},
            {LIST_CLASS.instance(init_contents=[
                {INT_CLASS.instance(), STR_CLASS.instance()}
            ])}
        )

    def test_list_indexing(self):
        """Test indexing a list."""
        code = """
x = [1, 3.0]
y = x[0]
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {INT_CLASS.instance(), FLOAT_CLASS.instance()}
        )

    def test_list_slicing(self):
        """Test slicing a list returns a copy of the list."""
        code = """
x = [1, 3.0]
y = x[0:1]
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("y"),
            {LIST_CLASS.instance(init_contents=[
                {INT_CLASS.instance()},
                {FLOAT_CLASS.instance()}
            ])}
        )

    def test_list_concatenation(self):
        """Test addition of 2 lists."""
        code = """
x = [1] + [3.0]
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {LIST_CLASS.instance(init_contents=[
                {INT_CLASS.instance(), FLOAT_CLASS.instance()}
            ])}
        )

    def test_list_appending(self):
        """Test appending to a list."""
        code = """
y = [3]
x = []
z = x.append(2)
"""
        env = ModuleEnv()
        env.parse_code(code)

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            env.exclusive_lookup("y")
        )

        self.assertSetEqual(
            env.exclusive_lookup("x"),
            {LIST_CLASS.instance(init_contents=[
                {INT_CLASS.instance()}
            ])}
        )

        self.assertSetEqual(
            env.exclusive_lookup("z"),
            {NONE_CLASS.instance()}
        )

#    def test_list_extend(self):
#        """Test extending a list with an iterable."""
#        code = """
#x = []
#y = x.extend([1])
#"""
#        env = ModuleEnv()
#        env.parse_code(code)
#
#        self.assertSetEqual(
#            env.exclusive_lookup("y"),
#            {NONE_CLASS.instance()}
#        )
#
#        self.assertSetEqual(
#            env.exclusive_lookup("x"),
#            {INT_CLASS.instance()}
#        )



if __name__ == "__main__":
    unittest.main()
