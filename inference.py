#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast

"""
Helper functions
"""

def first(iterable):
    return next(iter(iterable))


"""
Types available at runtime
"""

class PyType:
    def __init__(self, name, attrs=None):
        self.__name = name
        self.__attrs = attrs or {}  # dict[str, set[Instance]]

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
NONE_TYPE = PyType("None")
ANY_TYPE = PyType("Any")


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
        """For comparing instances at runtime."""
        raise NotImplementedError

    def __hash__(self):
        """For separating between different types in a set of instances."""
        raise NotImplementedError

    def returns(self):
        """The instances returned by this instance if it were called."""
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

class NoneInst(BaseInstance):
    def __init__(self):
        super().__init__(NONE_TYPE)

class AnyInst(BaseInstance):
    def __init__(self):
        super().__init__(ANY_TYPE)


# All types known to all environments
# Populated with builtin types initially and filled at runtime with user-defined
# types
TYPES = {
    "int": INT_TYPE,
    "float": FLOAT_TYPE,
    "complex": COMPLEX_TYPE,
    "None": NONE_TYPE,
}


class FunctionInst(Instance):
    def __init__(self, name, ref_node, ref_env, pos_args=None,
                 keyword_args=None, varargs=None, kwargs=None):
        """
        Create the new function type this instance represents since all
        function definitions are unique instances.

        Args:
            name (str)
            ref_node (ast.FunctionDef)
            ref_env (Environment): The environment this instance was created in

            pos_args (Optional[tuple[str]])
            keyword_args (Optional[dict[str, set[Instance]]])
            varargs (Optional[str])
            kwargs (Optional[str])
        """
        if name in TYPES:
            TYPES[name] |= PyType(name)
        else:
            TYPES[name] = {PyType(name)}

        self.__ref_node = ref_node
        self.__ref_env = ref_env

        # Save the arguments
        self.__pos_args = pos_args
        self.__keyword_args = keyword_args
        self.__varargs = varargs
        self.__kwargs = kwargs

        # Add the arguments as new variables with no types for now
        args = {}
        if pos_args:
            for arg in pos_args:
                args[arg] = set()
        if kwargs:
            for arg, vals in kwargs.items():
                args[arg] = vals
        if varargs:
            args[varargs] = {AnyInst()}  # should be tuple instance containing any type
        if kwargs:
            args[kwargs] = {AnyInst()}  # should be dict instance containing any type

        # The environment of this body
        self.__body_env = Environment(
            types=ref_env.types(),
            variables=args,
            parent=self.__ref_env,
        )

    @classmethod
    def from_node(cls, node, env):
        name = node.name
        args = node.args
        body = node.body

        if node.returns:
            # node.returns is an ast.Str
            returns = TYPES.get(node.returns.s, None)
        else:
            returns = None

        return cls(name, node, env)

    def apply_call_node_args(self, node):
        """
        Parse the arguments of a call node then apply_call_args.

        Args:
            args (node.Call)
        """
        raise NotImplementedError

    def apply_call_args(self, pos_args=None, keyword_args=None, varargs=None,
                        kwargs=None):
        """
        Update the environment of this body

        Args:
            pos_args (Optional[tuple[set[Instance]]])
            keyword_args (Optional[dict[str, set[Instance]]])
            varargs (Optional[str])
            kwargs (Optional[str])
        """
        raise NotImplementedError

    def returns(self):
        """
        Run through the code to find any return statements.
        """
        returns = set()

        stack = list(self.__ref_node.body)
        while stack:
            node = stack.pop()
            if isinstance(node, ast.Return):
                returns |= self.__ref_env.eval_inst(node.value)
            elif isinstance(node, (ast.If, ast.While, ast.For)):
                stack += node.body + node.orelse
            elif isinstance(node, ast.Try):
                stack += node.body + node.orelse + node.finalbody
                for handler in node.handlers:
                    stack += handler.body
            elif isinstance(node, ast.With):
                stack += node.body

        return returns or {NoneInst()}

    def __eq__(self, other):
        return id(self) == id(other)

    def __hash__(self):
        """All function instances are unique."""
        return id(self)


class Environment:
    def __init__(self, types=None, variables=None, parent=None):
        self.__types = types or TYPES
        self.__variables = variables or {}
        self.__parent = parent
        self.__uncalled_funcs = set()

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

    def parse_func_def(self, node):
        """
        Create a new function instance and add this one to a set of uncalled
        functions.
        """
        name = node.name
        func_inst = FunctionInst.from_node(node, self)  # This creates the instance and the type
        self.__uncalled_funcs.add(func_inst)

        # Add to env also
        self.bind(name, {func_inst})

    def parse(self, node):
        if isinstance(node, ast.Module):
            self.parse_module(node)
        elif isinstance(node, ast.Assign):
            self.parse_assign(node)
        elif isinstance(node, ast.FunctionDef):
            self.parse_func_def(node)
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

    def types(self):
        """
        Returns:
            dict[str, PyType]
        """
        return self.__types

    def variables(self):
        """
        Returns:
            dict[str, set[Instance]]
        """
        return self.__variables

