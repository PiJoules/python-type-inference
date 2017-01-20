#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from inference import ModuleEnv


class TestSamples(unittest.TestCase):
    def __env_from_file(self, filename):
        with open(filename, "r") as f:
            env = ModuleEnv()
            env.parse_code(f.read())
            return env

    def __env_json_from_file(self, filename):
        return self.__env_from_file(filename).json()

    def test_fib(self):
        """Test fibonacci script."""
        json = self.__env_json_from_file("samples/fib.py")
        self.assertListEqual(
            json["variables"]["fib"],
            ["fib"]
        )

        self.assertListEqual(
            json["types"]["fib"]["returns"],
            ["int"]
        )

        self.assertListEqual(
            json["types"]["fib"]["args"]["positional"],
            ["int"]
        )



if __name__ == "__main__":
    unittest.main()


