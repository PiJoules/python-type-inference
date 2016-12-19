#!/usr/bin/env python
# -*- coding: utf-8 -*-

from utils import *

import ast


class Type(object):
    """
    Class for performing delayed evaluation of types.
    This is a container of strings that is lazily evaluated.
    """
    def __init__(self, base_type):
        """
        Args:
            base_type (Type): Another type that this type is equivalent to.
        """
        self.__base = base_type

    def evaluate(self):
        """
        Returns:
            str
        """
        return self.__base.evaluate()


class AnyType(Type):
    def evaluate(self):
        return "Any"


class TypeInferer(object):
    def __init__(self, node, init_types=None):
        self.__types = init_types or {}
        self.__types = self.parse(node)

    def infer_list_type(self, lst):
        """
        Infer the contents of a list.
        """
        return {self.infer_type(expr) for expr in lst.elts}

    def infer_name_type(self, name):
        """
        Infer the type of a variable.
        """
        if name.id in self.__types:
            return self.__types[name.id]
        return {"Any"}

    def infer_unary_op(self, op):
        if isinstance(op.op, ast.Not):
            # If using Not, expression is always a boolean result
            return {"bool"}
        elif isinstance(op.op, ast.Invert):
            # Inversions only work on and return integers
            return {"int"}
        else:
            # Otherwise, the return value is either an int or float
            return self.infer_type(op.operand)

    def infer_binary_op(self, op):
        """
        This is tricky since these operations normally call magic methods
        which can be overriden in custom classes.

        TODO: Check if the type is builtin first. For now, the resulting types
        will just be either the resulting types of the left and right exprs.

        Returns:
            set[str]
        """
        return self.infer_type(op.left) | self.infer_type(op.right)

    def infer_type(self, expr):
        """
        Infer the types of a variable

        Returns:
            set[str]: Set of the types
        """
        if isinstance(expr, ast.Num):
            return {"int"}
        elif isinstance(expr, ast.Str):
            return {"str"}
        elif isinstance(expr, ast.Bytes):
            return {"bytes"}
        elif isinstance(expr, (ast.List, ast.Tuple, ast.Set)):
            return self.infer_list_type(self, expr)
        elif isinstance(expr, ast.NameConstant):
            return {str(expr.value)}
        elif isinstance(expr, ast.Name):
            return self.infer_name_type(expr)
        elif isinstance(expr, ast.Expr):
            return self.infer_type(expr.value)
        elif isinstance(expr, ast.UnaryOp):
            return self.infer_unary_op(expr)
        elif isinstance(expr, ast.BinOp):
            return self.infer_binary_op(expr)
        elif isinstance(expr, (ast.BoolOp, ast.Compare)):
            return {"bool"}

        return set()


    def parse_assign(self, asgn):
        targets = asgn.targets
        value = asgn.value
        val_type = self.infer_type(value)
        print("type:", val_type)
        raise NotImplementedError

    def parse_aug_assign(self, aug_asgn):
        raise NotImplementedError

    def parse_func_def(self, func_def):
        raise NotImplementedError

    def parse_class_def(self, cls_def):
        raise NotImplementedError

    def parse(self, node):
        """
        Wrapper for parsing all misceanious nodes.

        Args:
            node (ast.AST)

        Returns:
            dict
        """
        types = {}
        if isinstance(node, ast.Assign):
            return self.parse_assign(node)
        elif isinstance(node, ast.AugAssign):
            return self.parse_aug_assign(node)
        elif isinstance(node, ast.FunctionDef):
            return self.parse_func_def(node)
        elif isinstance(node, ast.ClassDef):
            return self.parse_class_def(node)
        elif isinstance(node, ast.Module):
            return self.parse_module(node)
        return types

    def parse_sequence(self, seq):
        """
        Parse nodes in a sequence of nodes.

        Args:
            seq (list[ast.AST])

        Returns:
            dict
        """
        types = {}
        for node in seq:
            types.update(self.parse(node))
        return types

    def parse_module(self, module):
        """
        Parse a module for types.

        Args:
            module (ast.Module)

        Returns:
            dict
        """
        return self.parse_sequence(module.body)

    def types(self):
        return self.__types



def main():
    sample = """
import keyword

x = 2

class C:
    pass

class D:
    pass

x = D()
    """

    tree = generate_ast(sample)
    prettyparseprint(sample)
    print(TypeInferer(tree))

    return 0


if __name__ == "__main__":
    main()

