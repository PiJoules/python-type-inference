#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils import *

import ast


class Type(object):
    """
    Class for performing delayed evaluation of types.
    This is a container of strings that is lazily evaluated.
    """
    def __init__(self, base_type="Any"):
        """
        Args:
            base_type (str, Type): Another type that this type is equivalent to.
        """
        if base_type is not None:
            self.__types = [base_type]
        else:
            self.__types = []

    def evaluate(self):
        """
        Returns:
            set[str]
        """
        types = set()
        for t in self.__types:
            if isinstance(t, str):
                types.add(t)
            else:
                types |= t.evaluate()
        return types

    def update(self, other):
        """Update the types in this container."""
        self.__types.append(other)

    def replace(self, other):
        """Replace all types in this container with another list of types."""
        self.__types = other

    def __str__(self):
        return str(self.evaluate())


class TypeInferer(object):
    def __init__(self, node, init_types=None):
        self.__types = init_types or {}
        self.__types = self.parse(node)

    def infer_list_type(self, lst, env):
        """
        Infer the contents of a list.
        """
        types = Type()
        for expr in lst.elts:
            types.update(self.infer_type(expr, env))
        return types

    def infer_name(self, name, env):
        """
        Infer the type of a variable.
        """
        if name.id in env:
            return env[name.id]
        return Type("Any")

    def infer_unary_op(self, op, env):
        if isinstance(op.op, ast.Not):
            # If using Not, expression is always a boolean result
            return Type("bool")
        elif isinstance(op.op, ast.Invert):
            # Inversions only work on and return integers
            return Type("int")
        else:
            # Otherwise, the return value is either an int or float
            return self.infer_type(op.operand, env)

    def infer_binary_op(self, op, env):
        """
        This is tricky since these operations normally call magic methods
        which can be overriden in custom classes.

        TODO: Check if the type is builtin first. For now, the resulting types
        will just be either the resulting types of the left and right exprs.

        Returns:
            Type
        """
        return self.infer_type(op.left, env).update(self.infer_type(op.right, env))

    def infer_call(self, call, env):
        return self.infer_name(call.func.name, env)

    def infer_num(self, num, env):
        if isinstance(num.n, int):
            return Type("int")
        elif isinstance(num.n, float):
            return Type("float")
        else:
            return Type("complex")

    def infer_attr(self, attr, env):
        """
        TODO: Will need to perform a search to find the type of an attribute
        in an object.
        """
        raise NotImplementedError

    def infer_type(self, expr, env):
        """
        Infer the types of a variable

        Returns:
            set[str]: Set of the types
        """
        if isinstance(expr, ast.Num):
            return self.infer_num(expr, env)
        elif isinstance(expr, ast.Str):
            return Type("str")
        elif isinstance(expr, ast.Bytes):
            return Type("bytes")
        elif isinstance(expr, (ast.List, ast.Tuple, ast.Set)):
            return self.infer_list_type(self, expr, env)
        elif isinstance(expr, ast.NameConstant):
            if expr.value is None:
                return Type("None")
            return Type("bool")
        elif isinstance(expr, ast.Name):
            return self.infer_name(expr, env)
        elif isinstance(expr, ast.Expr):
            return self.infer_type(expr.value, env)
        elif isinstance(expr, ast.UnaryOp):
            return self.infer_unary_op(expr, env)
        elif isinstance(expr, ast.BinOp):
            return self.infer_binary_op(expr, env)
        elif isinstance(expr, (ast.BoolOp, ast.Compare)):
            return Type("bool")
        elif isinstance(expr, ast.Call):
            return self.infer_call(expr, env)
        elif isinstance(expr, ast.Attribute):
            return self.infer_attr(expr)

        raise RuntimeError("Unable to determine type for expression '{}'".format(expr))

    def _update_type(self, env, var, t):
        if isinstance(t, Type):
            if var in env:
                env[var].update(t)
            else:
                env[var] = t
        elif isinstance(t, dict):
            if var in env:
                raise RuntimeError("Redefining variable '{}' with a function or class '{}'".format(var, t))
            env[var] = t
        else:
            raise RuntimeError("Unknown type '{}'".format(t))

    def parse_assign(self, asgn, env):
        targets = asgn.targets
        value = asgn.value
        val_type = self.infer_type(value, env)

        for target in targets:
            # target is ast.Name
            if isinstance(target, ast.Tuple):
                for elem in target:
                    self._update_type(env, elem.id, val_type)
            else:
                self._update_type(env, target.id, val_type)
        return env

    def parse_aug_assign(self, aug_asgn, env):
        """
        The types will be the combination of the existing types and the type
        of what is being added.
        """
        self._update_type(env, aug_asgn.target.id,
                          self.infer_type(aug_asgn.value, env))
        return env

    def parse_func_def(self, func_def, env):
        """
        TODO: Check for global and nonlocal variables
        """
        func_env = {}.update(env)
        #self._update_type(func_env, func_def.name, self.parse_sequence())
        #env
        return env

    def parse_class_def(self, cls_def, env):
        raise NotImplementedError

    def parse(self, node, env=None):
        """
        Wrapper for parsing all misceanious nodes.

        Args:
            node (ast.AST)

        Returns:
            dict
        """
        env = env or self.__types
        types = {}
        if isinstance(node, ast.Assign):
            return self.parse_assign(node, env)
        elif isinstance(node, ast.AugAssign):
            return self.parse_aug_assign(node, env)
        elif isinstance(node, ast.FunctionDef):
            return self.parse_func_def(node, env)
        elif isinstance(node, ast.ClassDef):
            return self.parse_class_def(node, env)
        elif isinstance(node, ast.Module):
            return self.parse_module(node, env)
        return types

    def parse_sequence(self, seq, env):
        """
        Parse nodes in a sequence of nodes.

        Args:
            seq (list[ast.AST])

        Returns:
            dict
        """
        types = {}
        for node in seq:
            types.update(self.parse(node, env))
        return types

    def parse_module(self, module, env):
        """
        Parse a module for types.

        Args:
            module (ast.Module)

        Returns:
            dict
        """
        return self.parse_sequence(module.body, env)

    def types(self):
        return self.__types



def main():
    sample = """
x = 2
x = "str"
    """

    tree = generate_ast(sample)
    prettyparseprint(sample)
    inferer = TypeInferer(tree)
    print(inferer.types())

    return 0


if __name__ == "__main__":
    main()

