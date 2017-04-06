#
#    code = """
#x = 2
#"""
#    env = ModuleEnv()
#    env.parse_code(code)

import ast
import astor

from environment import ModuleEnv


class Inferencer:
    def __init__(self, code_ast, **kwargs):
        self.__ast = code_ast
        self.__main_module = ModuleEnv(**kwargs)

    @classmethod
    def from_code(cls, code):
        return cls(ast.parse(code))
