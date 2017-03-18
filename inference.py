# -*- coding: utf-8 -*-

import ast
import sys
import os
import astor
import pytype
import arguments
import function_type
import class_type
import module_type


class Environment:
    def __init__(self, init_vars=None, parent_env=None,
                 module_location=None):
        self.__variables = dict(init_vars or {})  # dict[str, set[pytype.PyType]]
        self.__parent = parent_env
        if self.__parent:
            self.__call_stack = self.__parent.call_stack()
        else:
            self.__call_stack = set()

        # Initialize types known in the env
        self.__types = {}  # dict[str, pytype.PyType]
        for types in self.__variables.values():
            for t in types:
                self.__types[t.name()] = t

        # Modules
        self.__module_location = module_location

    def call_stack(self):
        return self.__call_stack

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

    def bind_attr(self, node, types):
        """
        Args:
            node (ast.Attribute)
            types (set[pytype.PyType])
        """
        value = node.value
        attr = node.attr

        value_types = self.eval(value)
        for t in value_types:
            t.add_attr(attr, types)

    def exclusive_lookup(self, varname):
        return self.__variables[varname]

    def lookup(self, varname):
        if varname in self.__variables:
            return self.exclusive_lookup(varname)

        if self.__parent:
            return self.__parent.lookup(varname)

        raise KeyError(varname)

    def exclusive_lookup_type(self, typename):
        return self.__types[typename]

    def lookup_type(self, typename):
        if typename in self.__types:
            return self.exclusive_lookup_type(typename)

        if self.__parent:
            return self.__parent.lookup_type(typename)

        raise KeyError(typename)

    def unpack_assign(self, target, types):
        if isinstance(target, ast.Name):
            self.bind(target.id, types)
        elif isinstance(target, ast.Attribute):
            self.bind_attr(target, types)
        else:
            raise NotImplementedError("Unable to assign to target node '{}'".format(target))


    """
    Type evaluation
    """

    def eval_num(self, node):
        n = node.n
        if isinstance(n, int):
            return {self.lookup_type("int")}
        else:
            raise NotImplementedError("Unknown type for num '{}'".format(type(n)))

    def eval_call(self, node):
        """
        Call, update, and evaluate the function.
        """
        ret_types = set()

        func_types = self.eval(node.func)  # set[PyType]

        args = arguments.Arguments.from_call_node(node, self)

        for func in func_types:
            if func not in self.__call_stack:
                self.__call_stack.add(func)
                if isinstance(func, function_type.FunctionType):
                    ret_types |= func.call_and_update(args)
                elif isinstance(func, class_type.ClassType):
                    ret_types |= func.create_and_init(args)
                else:
                    raise RuntimeError("Unknown callable type '{}'".format(type(func)))
                self.__call_stack.remove(func)

        return ret_types

    def eval_name(self, node):
        """
        Return a copy of the set.
        """
        return set(self.lookup(node.id))

    def eval_bin_op(self, node):
        """
        For now, just make the type the set containing both parts' types.

        TODO: Check the __op__ method of the left node
        """
        left = self.eval(node.left)
        right = self.eval(node.right)
        return left | right

    def eval_compare(self, node):
        """Always returns bools"""
        return self.lookup_type("bool")

    def eval_attr(self, node):
        value = node.value
        attr = node.attr

        value_types = self.eval(value)

        types = set()
        for t in value_types:
            types |= t.get_attr(attr)
        return types

    def eval_str(self, node):
        return {self.lookup_type("str")}

    def eval_subscript_index(self, node):
        idx_values = self.eval(node.slice.value)
        values = self.eval(node.value)

        ret_types = set()
        for value in values:
            ret_types |= value.get_idx(idx_values)
        return ret_types

    def eval_subscript(self, node):
        slice = node.slice
        if isinstance(slice, ast.Index):
            return self.eval_subscript_index(node)
        elif isinstance(slice, ast.Slice):
            return self.eval_subscript_slice(node)
        elif isinstance(slice, ast.ExtSlice):
            return self.eval_subscript_extslice(node)
        else:
            raise RuntimeError("Unknown slice type '{}'".format(slice))

    def eval_tuple(self, node):
        return {self.lookup_type("tuple").new_container(
            init_contents=tuple(self.eval(n) for n in node.elts)
        )}

    def eval(self, node):
        if isinstance(node, ast.Num):
            return self.eval_num(node)
        elif isinstance(node, ast.Call):
            return self.eval_call(node)
        elif isinstance(node, ast.Name):
            return self.eval_name(node)
        elif isinstance(node, ast.BinOp):
            return self.eval_bin_op(node)
        elif isinstance(node, ast.Compare):
            return self.eval_compare(node)
        elif isinstance(node, ast.Attribute):
            return self.eval_attr(node)
        elif isinstance(node, ast.Str):
            return self.eval_str(node)
        elif isinstance(node, ast.Subscript):
            return self.eval_subscript(node)
        elif isinstance(node, ast.Tuple):
            return self.eval_tuple(node)
        else:
            raise NotImplementedError("Unable to evaluate type for node '{}' on line {}".format(node, node.lineno))

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
            self.bind(kwarg_node.arg, set())

    def parse_assign(self, node):
        targets = node.targets
        val = node.value
        types = self.eval(val)

        for target in targets:
            self.unpack_assign(target, types)

    def parse_function_def(self, node):
        """
        Add a function type to the variables.
        """
        func_type = function_type.FunctionType.from_node_and_env(node, self)
        self.bind(node.name, {func_type})

    def parse_class_def(self, node):
        cls_type = class_type.ClassType.from_node_and_env(node, self)
        self.bind(node.name, {cls_type})

    def parse_if(self, node):
        """
        Evaluate the test then the bodies.
        """
        self.eval(node.test)
        self.parse_sequence(node.body)
        self.parse_sequence(node.orelse)

    def parse_expr(self, node):
        return self.eval(node.value)

    def parse_regular_import_alias(self, node):
        """
        Parse the imported module and make all variable assignments attributes
        of a new module type.
        """
        name = node.name
        asname = node.asname or name
        mod_t = module_type.load_module(name)
        self.bind(asname, {mod_t})

    def parse_import(self, node):
        for alias in node.names:
            asname = alias.asname
            if asname is None:
                self.parse_regular_import_alias(alias)
            else:
                raise NotImplementedError("No logic implemented yet for handling importing aliases")

    def parse(self, node):
        if isinstance(node, ast.Assign):
            self.parse_assign(node)
        elif isinstance(node, ast.FunctionDef):
            self.parse_function_def(node)
        elif isinstance(node, ast.arguments):
            self.parse_arguments(node)
        elif isinstance(node, ast.ClassDef):
            self.parse_class_def(node)
        elif isinstance(node, ast.If):
            self.parse_if(node)
        elif isinstance(node, ast.Expr):
            self.parse_expr(node)
        elif isinstance(node, ast.Import):
            self.parse_import(node)
        else:
            raise NotImplementedError("Unable to parse node '{}'".format(node))

    def parse_sequence(self, seq):
        for node in seq:
            self.parse(node)

    def parse_module(self, node):
        self.parse_sequence(node.body)

    def parse_code(self, code):
        self.parse_module(ast.parse(code))
        assert not self.__call_stack


class ModuleEnv(Environment):
    def __init__(self, module_location=None):
        super().__init__(init_vars=pytype.load_builtin_vars(),
                         module_location=module_location)

        # Also add this location to the pythonpath
        if module_location is not None:
            sys.path.insert(1, os.path.dirname(module_location))


