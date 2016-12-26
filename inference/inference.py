# -*- coding: utf-8 -*-

import ast_utils
import ast
import astor


"""
All types will have attributes that can map to types,
value types themselves, and return types when called.

Functions and classes are special types that contain nested environments.

Environments map all new variables to types contained in an internal container
for types such that all types that have new attributes added will refer to
the same types.

Python Control flow:
1. Go to next instruction.
2. If function definition, map the function name to a function object.
   If class definition, map class name to a class object and parse the code in
   a new environment that extends the current one.
3. If calling a function, parse the arguments for types if provided and
   evaluate the function code.
4. If calling a class, return an instance type and call the __init__ method
   if provided.

Elements in a class definition are added as attributes. Elements in an instance
are added as attributes but the first element automatically evaluates to the
object type itself.


class A:
    pass

x = A()
x.a = 1  # instance A contains attribute x of type int

From the variable name, will need to get the type, then from the type,
add the attribute.

y = A()
y.b = 1.0  # instance A contains attribute y of type float


def func():
    x = A()
    x.a = "str"  # instance A contains attribute x of type int or string

    Lookup the type of x to find it is an instance of A from the upper env.
    The property a of an instance A now can also be of type string.


- Keep the types and variables in separate containers because if different
  variables point to the same type object, there should be a separate container
  for types that hold the unique types to be edited. The variables will be a
  mapping of variable to type key and the types will be a mapping of type keys
  to the actual types.
- Neither the variables nor the types will be passed down/copied into lower
  environments. Lookup will instead involve keeping references to any parents
  and checking their variables/types if a variable is not located in the current
  env.
- Binding a variable to a type will involve adding the variable and type to
  the current env.
- Lookup for a variable will involve checking the current env then parents
- New types are added whenever a FunctionDef or ClassDef is found


class A:
    pass

def func():
    (some expr).attr = 2  # where some expr evaluates to instance A defined
                          # in an upper level


class A:  # id = 1
    pass

x = A()

class A:  # id = 2
    "redifinition"

x = A()  # x is of types A (id = 1) and A (id = 2)
THE MAPPING CANNOT BE A STRING. IT SHOULD BE A UNIQUE ID.


class A:
    pass

def func():
    x = A()
    x.a = 1

    class A:
        pass

    y = A()
    y.a = A()

- Types must respect scopes and only be available to environments on or below
  where they are declared, similar to variables.
- Type inference will involve looking for types declared in this env and
  looking in higher envs if not in the current one.


Creating a function:
def func():
    ...

is equivalent to defining a variable func that has the value "function" and
the return_type of whatever is returned by the body


Creating a class:
class A:
    ...

is equivalent to calling the contents of the class as if it were part of the
module body, but any variables assigned are attributes of the class itself.


Creating an instance:
x = A()

is equivalent to calling the contents of the __init__ of the A class. All
attributes in the class also belong to the instance, but the first argument
in all the function definitions are references to the class instance, including
the __init__ method.

"""


class ArgumentsInfo(object):
    pass


class Type(object):
    def __init__(self):
        self.__attrs = {}  # dict[str, set[int]]

    def value(self):
        """
        A hashable representation of this type.
        """
        raise NotImplementedError

    def return_type(self, args):
        """
        The type of variable returned if this type was called.

        TODO: Check python version since args change between 3.4 and 3.5.

        Args:
            args (ArgumentsInfo)

        Returns:
            set[int]
        """
        raise NotImplementedError

    def attrs(self):
        """
        Attributes of this type.
        """
        return self.__attrs

    def add_attr(self, attr, val):
        self.__attrs

    def environment(self):
        """
        The environment of variables and types in this type if it contains
        a body of statements.
        """
        raise NotImplementedError

    def __hash__(self):
        return hash(self.value())

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
        return not (self == other)


class FunctionType(Type):
    def __init__(self, node, env):
        self.__node = node
        self.__parent_env = env
        self.__hash = self.__generate_hash(node)

    def __generate_hash(self, node):
        """
        Generate the hash for this function once.

        Args:
            node (ast node)
        """
        return hash(astor.to_source(node))

    def value(self):
        return "function"

    def return_type(self, args):
        env = self.environment()

        types = set()

        # Find all return statements
        found_type = False
        stack = list(self.__node.body)
        while stack:
            node = stack.pop()
            if isinstance(node, ast.Return):
                t = env.infer_type(node.value)
                types.add(t)
                found_type = True
            elif isinstance(node, (ast.If, ast.While, ast.For)):
                stack += node.body + node.orelse
            elif isinstance(node, ast.Try):
                stack += node.body + node.orelse + node.finalbody
                for handler in node.handlers:
                    stack += handler.body
            elif isinstance(node, ast.With):
                stack += node.body

        return types

    @classmethod
    def from_node(cls, node):
        raise NotImplementedError

    def __hash__(self):
        return self.__hash


class ClassType(Type):
    pass


class InstanceType(Type):
    pass


"""
Builtin types
"""
class IntType(Type):
    def value(self):
        return "int"

class StrType(Type):
    def value(self):
        return "str"


def load_builtin_types():
    """
    Generate all types and variables available to an environment on startup.

    Returns:
        dict[str, Type]
    """
    return {
        "int": IntType(),
        "str": StrType(),
    }


class Environment(object):
    required_types = ("int", "str")

    def __init__(self, init_node=None, parent_env=None, required_types=None,
                 init_variables=None):
        """
        Args:
            required_types (dict[str, Type])
            init_variables (dict[str, Type])
        """
        self.__special_types = {}
        self.__parent = parent_env
        self.__types = {}
        self.__variables = {}

        self.__initialize_special_types(required_types or load_builtin_types())

        # Parse any initial variables passed through this env,
        # like args passed to a function
        init_variables = init_variables or {}
        for var, t in init_variables:
            type_id = self.__add_type(t)
            self.__variables[var] = type_id

        if init_node:
            self.parse(init_node)

    def __initialize_special_types(self, types):
        """
        Certain expressions can be automatically inferred without having to
        evaluate the expression itself. These types must be made available to
        the environment always, but always point to the same reference.
        """
        for type_name in self.required_types:
            type_id = self.__add_type(types[type_name])
            self.__special_types[type_name] = type_id

    def __add_type(self, t):
        """
        Add a type to the internal container for types and return a unique
        id representing the type and return this id.
        """
        type_id = self.__generate_id(t)
        if type_id in self.__types:
            raise RuntimeError("Existing type_id already in used for type")
        self.__types[type_id] = t
        return type_id

    def __generate_id(self, t):
        """
        Generate a unique id for a given type.

        Returns:
            int
        """
        return hash(t)

    def variables(self):
        """
        Mapping of variable name to type, where the type is an id that
        is used to keep types unique.

        Returns:
            dict[str, set[Type]]
        """
        variables = {}
        for var, type_ids in self.__variables.items():
            variables[var] = {self.type_from_id(id) for id in type_ids}
        return variables

    def parent_env(self):
        """
        An environment that this one can borrow variables from.

        Returns:
            Environment
        """
        return self.__parent

    def lookup(self, var):
        """
        Check the type of a variable.

        First look in current env then look at parents.

        Args:
            var (str): Variable name

        Returns:
            set[Type]: The type of the variable if it exists. None if
                not found.
        """
        variables = self.__variables
        if var in variables:
            # Combine all types
            # All ids of types this variable could be
            type_ids = variables[var]

            # Type lookup from id
            return {self.type_from_id(id) for id in type_ids}

        # Check parent_env
        parent_env = self.__parent
        if parent_env:
            return parent_env.lookup(var)

        raise RuntimeError("The variable '{}' was not previously declared.".format(var))

    def lookup_values(self, var):
        """
        The hashable representations of all types that a variable can be.
        """
        return {x.value() for x in self.lookup(var)}

    def __bind(self, var, type_id):
        """
        Bind a variable to a type in the environment.

        Args:
            var (str): Variable name
            type_id (int): Variable type

        Returns:
            None
        """
        variables = self.__variables
        if var in variables:
            variables[var].add(type_id)
        else:
            variables[var] = {type_id}

    def type_from_id(self, type_id):
        """
        Given an id for a type, find the actual reference to the type.

        Args:
            type_id (int)

        Returns:
            Type
        """
        types = self.__types
        if type_id in types:
            return types[type_id]

        parent_env = self.__parent
        if parent_env:
            return parent_env.type_from_id(type_id)

        raise RuntimeError("A type with the id '{}' does not exist.".format(type_id))

    def infer_name(self, num):
        """
        Returns:
            int
        """
        val = num.n
        if isinstance(val, int):
            return self.__special_types["int"]
        elif isinstance(val, float):
            return self.__special_types["float"]
        elif isinstance(val, complex):
            return self.__special_types["complex"]

        raise RuntimeError("Cannot infer Num type '{}'.".format(num))

    def infer_type(self, node):
        """
        Infer the type of an ast node.

        Will need to look in parent_env types.

        Args:
            node (ast node)

        Returns:
            set[int]: All possible types that this expression could be
        """
        if isinstance(node, ast.Num):
            return self.infer_name(node)
        elif isinstance(node, ast.Str):
            return self.__special_types["str"]
        raise NotImplementedError

    def parse_assign(self, node):
        """
        Returns:
            None
        """
        targets = node.targets
        value = node.value
        value_types = self.infer_type(value)

        for target in targets:
            # Handle variables only for now.
            # TODO: Handle variable unpacking later
            if isinstance(target, ast.Name):
                # Update the type of this variable in the env.
                self.__bind(target.id, value_types)

    def parse_sequence(self, nodes):
        for node in nodes:
            self.parse(node)

    def parse_func_def(self, node):
        raise NotImplementedError

    def parse(self, node):
        """
        Parse an ast node to update the current environment.

        Returns:
            None
        """
        if isinstance(node, ast.Module):
            self.parse_sequence(node.body)
        elif isinstance(node, ast.Assign):
            self.parse_assign(node)
        elif isinstance(node, ast.FunctionDef):
            self.parse_func_def(node)

    @classmethod
    def from_code(cls, code, **kwargs):
        return cls(init_node=ast.parse(code), **kwargs)


