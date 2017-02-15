# -*- coding: utf-8 -*-

import ast
import pytype
import arguments


class Environment:
    def __init__(self, init_vars=None, parent_env=None):
        self.__variables = dict(init_vars or {})  # dict[str, set[pytype.PyType]]
        self.__parent = parent_env

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
        return cls(init_vars=dict(parent_env.variables()))

    def variables(self):
        return self.__variables

    def bind(self, varname, types):
        assert isinstance(varname, str)
        assert isinstance(types, set)
        assert all(isinstance(x, pytype.PyType) for x in types)

        if varname in self.__variables:
            self.__variables[varname] |= types
        else:
            self.__variables[varname] = set(types)  # The types are always copied

    def exclusive_lookup(self, varname):
        return self.__variables[varname]

    def lookup(self, varname):
        if varname in self.__variables:
            return self.exclusive_lookup(varname)

        if self.__parent:
            return self.__parent.lookup(varname)

        raise KeyError(varname)

    def lookup_type(self, typename):
        return self.__types[typename]


    """
    Type evaluation
    """

    def eval_num(self, node):
        n = node.n
        if isinstance(n, int):
            return self.__types["int"]
        else:
            raise NotImplementedError("Unknown type for num '{}'".format(type(n)))

    def eval_call(self, node):
        """
        Call, update, and evaluate the function.
        """
        ret_types = set()
        args = arguments.Arguments.from_call_node(node, self)
        func_types = self.eval(node.func)  # set[PyType]
        for func in func_types:
            ret_types |= func.call_and_update(args)
        return ret_types

    def eval_name(self, node):
        """
        Return a copy of the set.
        """
        return set(self.__variables[node.id])

    def eval_bin_op(self, node):
        """
        For now, just make the type the set containing both parts' types.

        TODO: Check the __op__ method of the left node
        """
        left = self.eval(node.left)
        right = self.eval(node.right)
        return left | right

    def eval(self, node):
        if isinstance(node, ast.Num):
            return self.eval_num(node)
        elif isinstance(node, ast.Call):
            return self.eval_call(node)
        elif isinstance(node, ast.Name):
            return self.eval_name(node)
        elif isinstance(node, ast.BinOp):
            return self.eval_bin_op(node)
        else:
            raise NotImplementedError("Unable to evaluate type for node '{}'".format(node))

    """
    Node parsing
    """

    def parse_arguments(self, node):
        """
        Parse function definition arguments node.

        Positional arguments have no type by default (empty set) and
        keyword arguments have the default values as their only types.

        TODO: Check for type annotations later
        """
        # Positional args
        pos_args_end = len(node.args) - len(node.kwonlyargs)
        pos_args_nodes = node.args
        for arg_node in pos_args_nodes[:pos_args_end]:
            self.bind(arg_node.arg, set())

        # Varargs
        vararg_node = node.vararg
        if vararg_node:
            # Create a new tuple which could contain different types
            #self.bind(vararg_node.arg, {self.__types["tuple"].new_container()})
            self.bind(vararg_node.arg, set())

        # Keyword arguments
        for i, arg_node in enumerate(pos_args_nodes[pos_args_end:]):
            default_node = node.defaults[i]
            default_types = self.eval(default_node)
            self.bind(arg_node.arg, default_types)
        for i, kwarg_node in enumerate(node.kwonlyargs):
            default = node.kw_defaults[i]
            if default:
                types = self.eval(default)
            else:
                types = set()
            self.bind(kwarg_node.arg, types)

        # Kwargs
        kwarg_node = node.kwarg
        if kwarg_node:
            # Create a new dict which could contain different types
            #self.bind(kwarg_node.arg, {self.__types["dict"].new_container()})
            self.bind(kwarg_node.arg, set())

    def parse_assign(self, node):
        targets = node.targets
        val = node.value
        types = self.eval(val)

        for target in targets:
            if isinstance(target, ast.Name):
                self.bind(target.id, types)
            else:
                raise NotImplementedError("Unable to assign to target node '{}'".format(target))

    def parse_function_def(self, node):
        """
        Add a function type to the variables.
        """
        name = node.name
        func_type = pytype.FunctionType.from_node_and_env(node, self)
        self.bind(name, {func_type})

    def parse(self, node):
        if isinstance(node, ast.Assign):
            self.parse_assign(node)
        elif isinstance(node, ast.FunctionDef):
            self.parse_function_def(node)
        elif isinstance(node, ast.arguments):
            self.parse_arguments(node)
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


