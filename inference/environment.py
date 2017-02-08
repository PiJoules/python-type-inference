# -*- coding: utf-8 -*-

import ast
import inference


class Environment:
    """
    Class for keeping track of delcared variables
    """

    def __init__(self, init_variables=None, parent=None):
        self.__variables = dict(init_variables or {})  # defaultdict[str, set[Instance]]
        self.__parent_env = parent

    def lookup(self, varname):
        """
        Args:
            varname (str)

        Returns:
            (None, set[Instance])
        """
        if varname in self.__variables:
            return self.__variables[varname]

        if self.__parent_env:
            return self.__parent_env.lookup(varname)

        return None

    def bind(self, varname, vals):
        """
        Rules for assignment to a variable:
        https://docs.python.org/3/reference/simple_stmts.html#assignment-statements

        Args:
            varname (str)
            vals (set[Instance])
        """
        assert isinstance(vals, set)
        assert all(isinstance(x, inference.instance.Instance) for x in vals)

        if varname in self.__variables:
            self.__variables[varname] |= vals
        else:
            self.__variables[varname] = set(vals)


    """
    Instance evaluation from nodes
    """

    def eval_num(self, node):
        n = node.n
        if isinstance(n, int):
            return {inference.INT_CLASS.call()}
        elif isinstance(n, float):
            return {inference.FLOAT_CLASS.call()}
        elif isinstance(n, complex):
            raise NotImplementedError("Unable to evaluate number of type complex.")
        else:
            raise RuntimeError("Unknown type of number found from node '{}'".format(node))

    def eval(self, node):
        if isinstance(node, ast.Num):
            return self.eval_num(node)
        else:
            raise NotImplementedError("Unable to evaluate instance for node '{}'".format(node))


    """
    Parsing
    """

    def parse_assign(self, node):
        """
        Wrapper for bind given an assignment node.

        Rules for assignment:
        https://docs.python.org/3/reference/simple_stmts.html#assignment-statements

        Values can be assigned to:
        - Lists/tuples
        - Single variables
        - Subscriptions
        - Slices/ExtSlices
          - These are types of slices in a Subscription
        """
        targets = node.targets

        for target in targets:
            if isinstance(target, (ast.List, ast.Tuple)):
                raise NotImplementedError
            elif isinstance(target, ast.Name):
                # Simple call to bind
                insts = self.eval(node.value)
                self.bind(target.id, insts)
            elif isinstance(target, ast.Subscript):
                raise NotImplementedError
            else:
                raise RuntimeError("Unable to assign to target node '{}'".format(node))

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
    def __init__(self, **kwargs):
        super().__init__(init_variables=inference.instance.load_builtin_variables(),
                         **kwargs)
