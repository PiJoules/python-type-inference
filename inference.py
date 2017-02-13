# -*- coding: utf-8 -*-

import ast
import pytype


class Environment:
    def __init__(self, init_vars=None):
        self.__variables = dict(init_vars or {})  # dict[str, set[pytype.PyType]]

        # Initialize types known in the env
        self.__types = {}  # dict[str, pytype.PyType]
        for types in self.__variables.values():
            for t in types:
                self.__types[t.name()] = {t}

    @classmethod
    def from_parent_env(cls, parent_env):
        """
        Variables are copied over.
        """
        return cls(init_vars=dict(self.__variables))

    def bind(self, varname, types):
        assert isinstance(types, set)
        assert all(isinstance(x, pytype.PyType) for x in types)

        if varname in self.__variables:
            self.__variables[varname] |= types
        else:
            self.__variables[varname] = set(types)  # The types are always copied

    def lookup(self, varname):
        return self.__variables[varname]


    """
    Type evaluation
    """

    def eval_num(self, node):
        n = node.n
        if isinstance(n, int):
            return self.__types["int"]
        else:
            raise NotImplementedError("Unknown type for num '{}'".format(type(n)))

    def eval(self, node):
        if isinstance(node, ast.Num):
            return self.eval_num(node)
        else:
            raise NotImplementedError("Unable to evaluate type for node '{}'".format(node))

    """
    Node parsing
    """

    def parse_assign(self, node):
        targets = node.targets
        val = node.value
        types = self.eval(val)

        for target in targets:
            if isinstance(target, ast.Name):
                self.bind(target.id, types)
            else:
                raise NotImplementedError("Unable to assign to target node '{}'".format(target))

    def parse(self, node):
        if isinstance(node, ast.Assign):
            self.parse_assign(node)
        else:
            raise NotImplementedError("Unable to parse node '{}'".format(node))

    def parse_sequence(self, seq):
        for node in seq:
            self.parse(node)

    def parse_module(self, node):
        self.parse_sequence(node.body)

    def parse_code(self, code):
        self.parse_module(ast.parse(code))


class ModuleEnv(Environment):
    def __init__(self):
        super().__init__(init_vars=pytype.load_builtin_vars())


