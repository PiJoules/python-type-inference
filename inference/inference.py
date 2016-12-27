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


class Type(object):
    def __init__(self, ref_node=None, init_env=None):
        self.__attrs = {}  # dict[str, set[int]]
        self.__ref_node = ref_node

        # Parse default arguments
        # Arguments types are further infered in function calls in the
        # parse_call env
        self.__env = init_env

    def value(self):
        """
        A hashable representation of this type.
        """
        raise NotImplementedError

    def return_type(self):
        """
        The type of variable returned if this type was called.

        TODO: Check python version since args change between 3.4 and 3.5.

        Returns:
            set[Type]
        """
        if not self.__ref_node:
            raise RuntimeError("An reference node is required when calling this type.")
        env = self.environment()

        types = set()

        # Find all return statements
        found_type = False
        stack = list(self.__ref_node.body)
        while stack:
            node = stack.pop()
            if isinstance(node, ast.Return):
                types = env.infer_type(node.value)
                types |= types
                found_type = True
            elif isinstance(node, (ast.If, ast.While, ast.For)):
                stack += node.body + node.orelse
            elif isinstance(node, ast.Try):
                stack += node.body + node.orelse + node.finalbody
                for handler in node.handlers:
                    stack += handler.body
            elif isinstance(node, ast.With):
                stack += node.body

        # All types should be types
        assert all(isinstance(t, Type) for t in types)

        return types

    def attrs(self):
        """
        Attributes of this type.
        """
        return self.__attrs

    def add_attr(self, attr, val):
        """
        Args:
            attr (str)
            val (set[Type])
        """
        if attr not in self.__attrs:
            self.__attrs[attr] = val
        else:
            self.__attrs[attr] |= val

    def environment(self):
        """
        The environment of variables and types in this type if it contains
        a body of statements.

        Can be called with or without a node. If the call node is provided,
        more can be inferred about the types of the arguments.

        TODO: Handle decorators later
        """
        if not self.__env:
            raise RuntimeError("An initial environment is required when calling this type.")
        return self.__env

    def contents(self):
        """
        Returns:
            set[Type]
        """
        raise NotImplementedError

    def __hash__(self):
        return hash(self.value())

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
        return not (self == other)


class FunctionType(Type):
    def __init__(self, node, env, owner=None):
        """
        Args:
            node (ast.FunctionDef)
            env (Environment): The parent environment containing this type.
            owner (Optional[Type]): Provided if this type is a FunctionType
                that represents a method of an argument. If so, the first
                positional arg when this is called is always this owner.
        """
        args_dict = {}
        args_node = node.args

        # First argument refering to self
        pos_args = args_node.args
        if owner is None:
            start = 0
        else:
            start = 1
            args_dict[pos_args[0]] = owner
        end = len(pos_args) - len(args_node.defaults)

        # Positional args
        for arg in pos_args[start:end]:
            args_dict[arg.arg] = set()
        for i, arg in enumerate(pos_args[end:]):
            args_dict[arg.arg] = env.infer_type(args_node.defaults[i])

        # Keyword args
        keyword_args = args_node.kwonlyargs
        defaults = args_node.kw_defaults
        for i, kwarg in enumerate(keyword_args):
            if defaults[i] is None:
                args_dict[kwarg.arg] = {env.special_types()["Any"]}
            else:
                args_dict[kwarg.arg] = defaults[i]

        # Vararg and kwargs
        if args_node.vararg:
            args_dict[args_node.vararg.arg] = {env.special_types()["tuple"]}
        if args_node.kwarg:
            args_dict[args_node.kwarg.arg] = {env.special_types()["dict"]}

        env = Environment.from_env(env, init_variables=args_dict)

        super().__init__(ref_node=node, init_env=env)

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


class AnyType(Type):
    def value(self):
        return "Any"


class TupleType(Type):
    """
    A type that can contain different types.
    """
    def __init__(self, default, content_types=None):
        """
        Args:
            default (Type): The default type of the contents of this type
                if this type does not contain anything.
            content_types (Optional[set[type]])
        """
        super().__init__()
        self.__contents = content_types or set()
        self.__default = default

    def contents(self):
        """
        Returns:
            set[Type]
        """
        if self.__contents:
            return self.__contents
        else:
            return {self.__default}

    def value(self):
        return "tuple"


class DictType(ClassType):
    """
    A type that can contains a mapping of different types.
    """
    def __init__(self, key_default, value_default, key_contents=None,
                 value_contents=None):
        """
        Args:
            default (Type): The default type of the contents of this type
                if this type does not contain anything.
            content_types (Optional[set[type]])
        """
        super().__init__()
        self.__key_contents = key_contents or set()
        self.__value_contents = value_contents or set()
        self.__key_def = key_default
        self.__val_def = value_default

    def key_contents(self):
        """
        Returns:
            set[Type]
        """
        if self.__key_contents:
            return self.__key_contents
        else:
            return {self.__key_def}

    def value_contents(self):
        """
        Returns:
            set[Type]
        """
        if self.__value_contents:
            return self.__value_contents
        else:
            return {self.__val_def}

    def value(self):
        return "dict"


def load_builtin_types():
    """
    Generate all types and variables available to an environment on startup.

    Returns:
        dict[str, Type]
    """
    any_type = AnyType()
    return {
        "int": IntType(),
        "str": StrType(),
        "Any": any_type,
        "tuple": TupleType(any_type),
        "dict": DictType(any_type, any_type),
    }


class Environment(object):
    required_types = ("int", "str", "Any", "tuple", "dict")

    def __init__(self, init_node=None, parent_env=None, required_types=None,
                 init_variables=None):
        """
        Args:
            required_types (dict[str, Type])
            init_variables (dict[str, set[Type]])
        """
        self.__special_types = {}
        self.__parent = parent_env
        self.__types = {}
        self.__variables = init_variables or {}

        self.__initialize_special_types(required_types or load_builtin_types())

        if init_node:
            self.parse(init_node)

    @classmethod
    def from_env(cls, env, **kwargs):
        return cls(
            parent_env=env,
            required_types=env.special_types(),
            **kwargs
        )

    def special_types(self):
        return self.__special_types

    def __initialize_special_types(self, types):
        """
        Certain expressions can be automatically inferred without having to
        evaluate the expression itself. These types must be made available to
        the environment always, but always point to the same reference.
        """
        for type_name in self.required_types:
            self.__special_types[type_name] = types[type_name]

    def variables(self):
        """
        Mapping of variable name to type, where the type is an id that
        is used to keep types unique.

        Returns:
            dict[str, set[Type]]
        """
        return self.__variables

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
            types = variables[var]
            if not types:
                # Empty set
                # This is a result of positional args that weren't evaluated
                # More with function calls.
                return {self.__special_types["Any"]}
            else:
                return types

        # Check parent_env
        parent_env = self.__parent
        if parent_env:
            return parent_env.lookup(var)

        raise RuntimeError("The variable '{}' was not previously declared.".format(var))

    def simple_lookup(self, var):
        """
        If a varibale contains only one type, it returns that type instead of
        the whole set containing one item. Otherwise, it returns the whole set.

        Meant for debugging purposes external to this class.
        """
        types = self.lookup(var)
        if len(types) == 1:
            return next(iter(types))
        return types

    def lookup_return_type_values(self, var):
        """
        Call .return_type() on each of the types a variable can be then
        .value()
        """
        types = self.lookup(var)  # All types of this variable
        ret_types = set()  # All return types of these types
        for t in types:
            ret_types |= t.return_type()
        ret_type_vals = {t.value() for t in ret_types}
        return ret_type_vals

    def lookup_values(self, var):
        """
        The hashable representations of all types that a variable can be.

        Call .value() on each of the types a variable can be.
        """
        return {x.value() for x in self.lookup(var)}

    def __bind(self, var, t):
        """
        Bind a variable to a type in the environment.

        Args:
            var (str): Variable name
            t (set[Type]): Variable types

        Returns:
            None
        """
        variables = self.__variables
        if var in variables:
            variables[var] |= t
        else:
            variables[var] = t

    def infer_num(self, num):
        """
        Returns:
            set[Type]
        """
        val = num.n
        if isinstance(val, int):
            return {self.__special_types["int"]}
        elif isinstance(val, float):
            return {self.__special_types["float"]}
        elif isinstance(val, complex):
            return {self.__special_types["complex"]}

        raise RuntimeError("Cannot infer Num type '{}'.".format(num))

    def infer_name(self, node):
        """
        Essentially a variable lookup.
        """
        return self.lookup(node.id)

    def infer_type(self, node):
        """
        Infer the type of an ast node.

        Will need to look in parent_env types.

        Args:
            node (ast node)

        Returns:
            set[Type]: All possible types that this expression could be
        """
        if isinstance(node, ast.Num):
            return self.infer_num(node)
        elif isinstance(node, ast.Str):
            return {self.__special_types["str"]}
        elif isinstance(node, ast.Name):
            return self.infer_name(node)

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
        """
        Create a new functiont type and add it to the env.
        """
        self.__bind(node.name, {FunctionType(node, self)})

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


