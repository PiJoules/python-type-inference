#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast


"""
Types available at runtime
"""

class PyType:
    def __init__(self, name, attrs=None):
        self.__name = name
        self.__attrs = attrs or {}  # dict[str, set[PyType]]

    def name(self):
        return self.__name

    def add_attr(self, attr, val):
        """
        Add an attribute to this type of object.

        Args:
            attr (str)
            val (PyType)
        """
        self.__add_attrs(attr, {val})

    def add_attrs(self, attr, vals):
        """
        Add mutliple values for a given attribute to the type.

        Args:
            attr (str)
            val (set[PyType]))
        """
        if attr not in self.__attrs:
            self.__attrs[attr] = vals
        else:
            self.__attrs[attr] |= vals

    def get_attr(self, attr):
        return self.__attrs[attr]

    def attrs(self):
        return self.__attrs


INT_TYPE = PyType("int")
FLOAT_TYPE = PyType("float")
COMPLEX_TYPE = PyType("complex")


"""
Instances created at runtime or are builtin instances available at startup
"""

class Instance:
    def __init__(self, inst_type):
        self.__type = inst_type

    def type(self):
        return self.__type

    def __ne__(self, other):
        return not (self == other)

    def __eq__(self, other):
        raise NotImplementedError

    def __hash__(self):
        raise NotImplementedError


class BaseInstance(Instance):
    """Instances of types where the runtime properties do not matter."""
    def __eq__(self, other):
        return isinstance(other, type(self))

    def __hash__(self):
        """Hash is just a hash of the name of this type of instance."""
        return hash(self.type().name())


class IntInst(BaseInstance):
    def __init__(self):
        super().__init__(INT_TYPE)

class FloatInst(BaseInstance):
    def __init__(self):
        super().__init__(FLOAT_TYPE)

class ComplexInst(BaseInstance):
    def __init__(self):
        super().__init__(COMPLEX_TYPE)


TYPES = {
    "int": INT_TYPE,
    "float": FLOAT_TYPE,
    "complex": COMPLEX_TYPE,
}


class Environment:
    def __init__(self, types=None, variables=None, parent=None):
        self.__types = types or {}
        self.__variables = variables or {}
        self.__parent = parent

    @classmethod
    def from_env(cls, env, **kwargs):
        raise NotImplementedError

    def bind(self, var, insts):
        assert isinstance(insts, set)
        assert all(isinstance(x, Instance) for x in insts)

        if not var in self.__variables:
            self.__variables[var] = insts
        else:
            self.__variables[var] |= insts


    """
    Type inference
    """

    def eval_num(self, node):
        n = node.n
        if isinstance(n, int):
            return {IntInst()}
        elif isinstance(n, float):
            return {FloatInst()}
        elif isinstance(n, complex):
            return {ComplexInst()}
        else:
            raise RuntimeError("Unknown num type {}".format(n))

    def eval_inst(self, node):
        if isinstance(node, ast.Num):
            return self.eval_num(node)
        else:
            raise NotImplementedError("Unable to infer type for node {}".format(node))


    """
    Parsing ast
    """

    def parse_assign(self, node):
        """
        TODO: Unpack variables during assignment.
        """
        targets = node.targets
        value = node.value  # ast node
        insts = self.eval_inst(value)

        for target in targets:
            if isinstance(target, ast.Name):
                self.bind(target.id, insts)
            else:
                raise NotImplementedError("Unable to assign to target node {}".format(node))

    def parse(self, node):
        if isinstance(node, ast.Module):
            self.parse_module(node)
        elif isinstance(node, ast.Assign):
            self.parse_assign(node)
        else:
            raise NotImplementedError("Cannot parse node {}".format(node))

    def parse_sequence(self, seq):
        for node in seq:
            self.parse(node)

    def parse_module(self, node):
        self.parse_sequence(node.body)

    def parse_code(self, code):
        self.parse(ast.parse(code))


    """
    Getters
    """

    def lookup(self, var, ignore_parent=False):
        if var in self.__variables:
            return self.__variables[var]

        if not ignore_parent and self.__parent:
            return self.__parent.lookup(var)

        return None

