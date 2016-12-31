# -*- coding: utf-8 -*-

import object_types
import objects
from ast_utils import prettyparsetext

import ast


class Inferer(object):
    """
    Wrapper class for initializing builin functions and types once.
    """

    def __init__(self):
        types = self.__load_builtin_types()
        self.__env = Environment(
            init_variables=self.__load_builtin_variables(),
            init_types=types,
        )

    def __load_builtin_variables(self):
        """
        For functions and constants like tuple(), int(), map(), etc.
        """
        return {
        }

    def __load_builtin_types(self):
        """
        These should all be initialized once in the lifespan of this object.

        Returns:
            dict[str, Type]
        """
        types = [
            object_types.IntType(),
            object_types.ListType(),
            object_types.FloatType(),
        ]
        return {t.name(): t for t in types}

    def environment(self):
        return self.__env


class Environment(object):
    def __init__(self, init_variables=None, init_types=None, parent_env=None):
        """
        The init types must always be passed down to nested envs.

        Args:
            init_variables (Optional[dict[str, set[Object]]])
            init_types (Optional[dict[str, Type]])
        """
        self.__variables = init_variables or {}
        self.__types = init_types or {}
        self.__parent = parent_env

    def bind(self, var, objs):
        """
        Bind a variable to an object in the environment.

        Args:
            var (str): Variable name
            objs (set[Object]): Objects

        Returns:
            None
        """
        assert isinstance(objs, set)
        assert all(isinstance(o, objects.Object) for o in objs)

        variables = self.__variables
        if var in variables:
            variables[var] |= objs
        else:
            variables[var] = set(objs)

    """
    Type inference
    """

    def infer_num(self, node):
        """
        Returns:
            set[Object]
        """
        val = node.n
        if isinstance(val, int):
            return {self.__types["int"].new_obj()}
        elif isinstance(val, float):
            return {self.__types["float"].new_obj()}
        elif isinstance(val, complex):
            return {self.__types["complex"].new_obj()}

        raise RuntimeError("Cannot infer Num type '{}'.".format(num))

    def infer_list(self, node):
        """
        Returns:
            set[ListObject]
        """
        return {self.__special_objs["list"](self.__types["Any"], [self.infer_obj(n) for n in node.elts])}

    def infer_name(self, node):
        objs = self.lookup_objs(node.id)
        if objs is not None:
            return objs
        raise RuntimeError("Variable {} not previously declared".format(node.id))

    def infer_obj(self, node, call_stack=None):
        """
        Infer the type of an ast node.

        Will need to look in parent_env types.

        Args:
            node (ast node)

        Returns:
            set[Object]: All possible objects that this expression could be
        """
        call_stack = call_stack or set()
        if isinstance(node, ast.Num):
            return self.infer_num(node)
        elif isinstance(node, ast.Str):
            return {self.__types["str"]}
        elif isinstance(node, ast.Name):
            return self.infer_name(node)
        elif isinstance(node, ast.Call):
            return self.infer_call(node, call_stack=call_stack)
        elif isinstance(node, ast.Attribute):
            return self.infer_attribute(node, call_stack=call_stack)
        elif isinstance(node, ast.BinOp):
            return self.infer_binary_operation(node, call_stack=call_stack)
        elif isinstance(node, ast.Tuple):
            return self.infer_tuple(node, call_stack=call_stack)

        raise RuntimeError("Unable to infer type for node '{}'\n{}"
                           .format(node, prettyparsetext(node)))

    """
    Parsing
    """

    def parse_sequence(self, seq):
        for node in seq:
            self.parse(node)

    def parse_module(self, node):
        self.parse_sequence(node.body)

    def parse_assign(self, node):
        targets = node.targets
        value = node.value
        value_types = self.infer_obj(value)

        for target in targets:
            # Handle variables only for now.
            # TODO: Handle variable unpacking later
            if isinstance(target, ast.Name):
                # Update the type of this variable in the env.
                self.bind(target.id, value_types)
            elif isinstance(target, ast.Attribute):
                # Add the attribute to the type
                raise NotImplementedError
                #types = self.infer_obj(target.value)
                #for t in types:
                #    t.add_attr(target.attr, value_types)

    def parse_func_def(self, node):
        """
        Create a new function type and add it to the env.
        """
        #self.bind(node.name, {FunctionObject(node, self, owner=self.__owner)})
        raise NotImplementedError

    def parse(self, node):
        """
        Update the environment given an ast node.

        Args:
            node (ast node)

        Returns:
            None
        """
        if isinstance(node, ast.Module):
            self.parse_module(node)
        elif isinstance(node, ast.Assign):
            self.parse_assign(node)
        elif isinstance(node, ast.FunctionDef):
            self.parse_func_def(node)
        else:
            raise NotImplementedError("No logic yet for parsing node {}".format(node))

    def parse_code(self, code):
        """
        Convert a string to an ast node then parse it.
        """
        self.parse(ast.parse(code))

    """
    Environment lookups
    """

    def lookup_objs(self, var):
        objs = self.__variables.get(var, None)
        if objs is not None:
            return objs

        # Check parent envs
        if self.__parent is not None:
            return self.__parent.lookup_objs(var)

        return None

    def lookup_types(self, var):
        """
        Lookup a variable in the environment.

        Lookup the current one first then the parents.

        Args:
            var (str)

        Returns:
            (None, set[Type]): None if does not exist.
        """
        objs = self.lookup_objs(var)
        if objs is not None:
            # Get all the types
            types = set()
            for obj in objs:
                types |= obj.types()
            return types

        # Check parent envs
        if self.__parent is not None:
            return self.__parent.lookup_types(var)

        return None

