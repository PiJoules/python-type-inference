# -*- coding: utf-8 -*-

from .ast_utils import prettyparsetext
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


def simple(types):
    """
    If the container contains only 1 item, return that item instead of the
    container. Otherwise, return the whole container.
    """
    if len(types) == 1:
        return next(iter(types))
    return types


class Type(object):
    def __init__(self):
        self.__attrs = {}  # dict[str, set[int]]

    def json(self, call_stack=None):
        return {
            "value": self.value(),
            "attrs": self.attrs(),
        }

    def value(self):
        """
        A hashable representation of this type.
        """
        raise NotImplementedError

    def return_type(self, call_stack=None):
        """
        The type of variable returned if this type was called.

        TODO: Check python version since args change between 3.4 and 3.5.

        Returns:
            set[Type]
        """
        raise NotImplementedError

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
        assert isinstance(val, set)
        assert all(isinstance(t, Type) for t in val)

        if attr not in self.__attrs:
            self.__attrs[attr] = val
        else:
            self.__attrs[attr] |= val

    def get_attr(self, attr, default=None):
        """
        Returns:
            set[Type]
        """
        return self.__attrs.get(attr, default)

    def __hash__(self):
        """
        This hash is for comparing against the different types that
        exist within the environment.
        """
        raise NotImplementedError

    def __eq__(self, other):
        return isinstance(other, type(self)) and (hash(self) == hash(other))

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
        super().__init__()
        self.__hash = self.__generate_hash(node)
        self.__node = node

        args_dict = {}
        args_node = node.args

        # First argument refering to self
        pos_args = args_node.args
        if owner is None:
            start = 0
        else:
            start = 1
            args_dict[pos_args[0].arg] = {owner}
        end = len(pos_args) - len(args_node.defaults)

        # Positional args
        for arg in pos_args[start:end]:
            args_dict[arg.arg] = set()
        for i, arg in enumerate(pos_args[end:]):
            args_dict[arg.arg] = env.infer_type(args_node.defaults[i])

        self.__positional = [a.arg for a in pos_args[start:]]  # list[str]

        # Keyword args
        keyword_args = args_node.kwonlyargs
        defaults = args_node.kw_defaults
        for i, kwarg in enumerate(keyword_args):
            if defaults[i] is None:
                args_dict[kwarg.arg] = set()
            else:
                args_dict[kwarg.arg] = env.infer_type(defaults[i])

        # Vararg and kwargs
        if args_node.vararg:
            args_dict[args_node.vararg.arg] = {env.special_types()["container"]}
        if args_node.kwarg:
            args_dict[args_node.kwarg.arg] = {env.special_types()["dict"]}

        # Checks on the args_dict
        for k, v in args_dict.items():
            assert isinstance(k, str)
            assert isinstance(v, set)
            assert all(isinstance(t, Type) for t in v)

        # Function envs are parsed on creation
        func_env = Environment.from_env(env, init_variables=args_dict)
        func_env.parse_sequence(node.body)
        self.__env = func_env

    def return_type(self, call_stack=None):
        """
        The type of variable returned if this type was called.

        TODO: Check python version since args change between 3.4 and 3.5.

        Returns:
            set[Type]
        """
        call_stack = call_stack or set()
        env = self.__env

        types = set()

        # Find all return statements
        # Use boolean instead of checking empty types because infer_type()
        # could return an empty set
        found_type = False
        stack = list(self.__node.body)
        while stack:
            node = stack.pop()
            if isinstance(node, ast.Return):
                types = env.infer_type(node.value, call_stack=call_stack)
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

        if not found_type:
            return {env.special_types()["None"]}

        return types

    def environment(self):
        return self.__env

    def json(self, call_stack=None):
        call_stack = call_stack or set()

        if self not in call_stack:
            call_stack.add(self)
            env_json = self.__env.json(call_stack=call_stack)
        else:
            env_json = "Recursive loop stop for this function."

        return {
            "value": self.value(),
            "attrs:": self.attrs(),
            "environment": env_json,
        }

    def apply_call_args(self, node):
        """
        Updatee the variables in an environment based on what is passed to
        a call to this function.

        Args:
            node (ast.Call)
        """
        env = self.__env

        # Apply positional
        """
        In rare cases where functions are passed as the argument,
        the number of args provided to a function could exceed the
        number of positional arguments defined in the function def.

        Iterate up to the number of positional arguments defined.
        Otherwise, an IndexError cold be thrown, like for the following
        example:

        def func(arg, arg2):
            return arg(arg, arg2)
        x = func(func, 5j)
        def func(a):
            return a(a)
        x = func(func)

        This is systactically valid, but throws an IndexError if not iterating
        up to the number of defined positional args.
        """
        for i, arg in enumerate(node.args[:len(self.__positional)]):
            env.bind(self.__positional[i], env.infer_type(arg))

        # Apply keyword
        for kwarg in node.keywords:
            env.bind(kwarg.arg, env.infer_type(kwarg.value))

        # Re-evaluate the body
        env.parse_sequence(self.__node.body)

    def __generate_hash(self, node):
        """
        Generate the hash for this function once.

        Args:
            node (ast node)
        """
        return hash(astor.to_source(node))

    def value(self):
        return "function"

    def __hash__(self):
        return self.__hash


class ClassType(Type):
    def __init__(self, node, env):
        """
        All variables assigned in this env are attributes of this type and
        its instance.
        """
        super().__init__()
        self.__hash = self.__generate_hash(node)
        self.__node = node
        self.__env = env
        self.__instances = []

        # This env should not persist outside this function. It is only used
        # for finding the attributes of this class.
        new_env = Environment.from_env(env)
        new_env.parse_sequence(node.body)
        for var, types in new_env.variables().items():
            #self.add_attr(var, types)
            self.add_class_attr(var, types)

    def add_class_attr(self, attr, val):
        """Add any new attribute only to the class."""
        super().add_attr(attr, val)

    def add_attr(self, attr, val):
        self.__cls_type.add_class_attr(attr, val)
        self.add_instance_attr(attr, val)

    def value(self):
        return "type"

    def return_type(self, call_stack=None):
        return {InstanceType(self.__node, self.__env, self)}

    def __generate_hash(self, node):
        """
        Generate the hash for this function once.

        Args:
            node (ast node)
        """
        return hash(astor.to_source(node))

    def __hash__(self):
        return self.__hash


class InstanceType(Type):
    def __init__(self, node, env, cls_type):
        """
        Create an instance from a class.

        The methods are automatically parsed on the FunctionType creation in
        the environment parse.
        """
        super().__init__()
        self.__name = node.name
        self.__cls_type = cls_type

        new_env = Environment.from_env(env, owner=self)
        new_env.parse_sequence(node.body)
        for var, types in new_env.variables().items():
            #self.add_attr(var, types)
            self.add_instance_attr(var, types)

    def add_instance_attr(self, attr, val):
        """Add any new attribute only to the instance."""
        super().add_attr(attr, val)

    def add_attr(self, attr, val):
        self.__cls_type.add_class_attr(attr, val)
        self.add_instance_attr(attr, val)

    #def get_attr(self, attr, default=None):
    #    """First check the instance then check the class."""
    #    val = super().get_attr(attr)
    #    if val is None:
    #        # Check class
    #        return self.__cls_type.get_attr(attr, default=default)
    #    return val

    def value(self):
        return self.__name

    def __hash__(self):
        return hash(self.value())


"""
Builtin types
"""
class LiteralType(Type):
    def __hash__(self):
        return hash(self.value())


class IntType(LiteralType):
    def value(self):
        return "int"


class FloatType(LiteralType):
    def value(self):
        return "float"


class ComplexType(LiteralType):
    def value(self):
        return "complex"


class StrType(LiteralType):
    def value(self):
        return "str"


class AnyType(LiteralType):
    def value(self):
        return "Any"


class NoneType(LiteralType):
    def value(self):
        return "None"


class ContainerType(Type):
    """
    A type that can contain different types. This container is meant to hold
    an undefined number of data types.

    Lists/sets
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
        return "container"

    def __hash__(self):
        """All containers are based off their contents."""
        return id(self)


class ContainerInstance(Type):
    pass


class TupleType(Type):
    """
    Similar to a ContainerType but order and number of contents matter.
    """
    def __init__(self, node, env, owner=None):
        """
        All variables assigned in this env are attributes of this type and
        its instance.
        """
        super().__init__()
        self.__hash = self.__generate_hash(node)

        # This env should not persist outside this function. It is only used
        # for finding the attributes of this class.
        new_env = Environment.from_env(env)
        new_env.parse_sequence(node.body)
        for var, types in new_env.variables().items():
            self.add_attr(var, types)

        self.__instance = InstanceType(node, env)

    def value(self):
        return "type"

    def return_type(self, call_stack=None):
        return {self.__instance}

    def __generate_hash(self, node):
        """
        Generate the hash for this function once.

        Args:
            node (ast node)
        """
        return hash(astor.to_source(node))

    def __hash__(self):
        return self.__hash


class TupleInstance(Type):
    pass


class DictType(Type):
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

    def __hash__(self):
        return hash(self.value())


def load_builtin_types():
    """
    Generate all types and variables available to an environment on startup.

    Returns:
        dict[str, Type]
    """
    any_type = AnyType()
    return {
        "int": IntType(),
        "float": FloatType(),
        "complex": ComplexType(),
        "str": StrType(),
        "Any": any_type,
        "None": NoneType(),
        "container": ContainerType(any_type),
        #"tuple": TupleType(),
        "dict": DictType(any_type, any_type),
    }


class Environment(object):
    required_types = tuple(load_builtin_types().keys())

    def __init__(self, init_node=None, parent_env=None, required_types=None,
                 init_variables=None, owner=None):
        """
        Args:
            required_types (dict[str, Type])
            init_variables (dict[str, set[Type]])
            owner (Optional[InstanceType])
        """
        self.__special_types = {}
        self.__parent = parent_env
        self.__types = {}
        self.__variables = dict(**(init_variables or {}))  # Copy the dict

        assert (owner is None) or isinstance(owner, InstanceType)
        self.__owner = owner

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

    def lookup(self, var, ignore_parent=False):
        """
        Check the type of a variable.

        First look in current env then look at parents.

        Args:
            var (str): Variable name
            ignore_parent (bool): If the parent env exists, do not check it if
                the this is true and the variable is not in this env.

        Returns:
            set[Type]: The type of the variable if it exists. None if
                not found.
        """
        variables = self.__variables
        if var in variables:
            types = variables[var]
            # This could result in an empty set.
            # Empty sets could be found for positional arguments of functions
            # that aren't called.
            return types

        # Check parent_env
        parent_env = self.__parent
        if parent_env and not ignore_parent:
            return parent_env.lookup(var)

        return set()

    def lookup_values(self, var):
        """
        The hashable representations of all types that a variable can be.

        Call .value() on each of the types a variable can be.
        """
        return {x.value() for x in self.lookup(var)}

    def bind(self, var, types):
        """
        Bind a variable to a type in the environment.

        Args:
            var (str): Variable name
            t (set[Type]): Variable types

        Returns:
            None
        """
        assert isinstance(types, set)
        assert all(isinstance(t, Type) for t in types)

        variables = self.__variables
        if var in variables:
            variables[var] |= types
        else:
            variables[var] = types

    def infer_num(self, node):
        """
        Returns:
            set[Type]
        """
        val = node.n
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

        Copy contents into a new set since variables assigned to variables
        are unaffected by reassignments of the second variables.
        """
        return set(self.lookup(node.id))

    def infer_call(self, node, call_stack=None):
        """
        First change the function environment based on the argument,
        then evaluate.

        Returns:
            set[Type]
        """
        self.parse_call(node)
        call_stack = call_stack or set()
        ret_types = set()

        if node not in call_stack:
            call_stack.add(node)
            types = self.infer_type(node.func, call_stack=call_stack)
            for t in types:
                if isinstance(t, (FunctionType, ClassType)):
                    ret_types |= t.return_type(call_stack=call_stack)

        return ret_types

    def infer_attribute(self, node, call_stack=None):
        """
        Returns:
            set[Type]
        """
        value = node.value  # ast node
        attr = node.attr  # str
        attr_types = set()
        call_stack = call_stack or set()
        value_types = self.infer_type(value, call_stack=call_stack)

        for t in value_types:
            attr_type = t.get_attr(attr)
            if attr_type is not None:
                attr_types |= attr_type

        return attr_types

    def infer_binary_operation(self, node, call_stack=None):
        """
        The common binary operations call the respective magic method of the
        left hand side object. For now, just return the set containing the
        possible types of both expressions.
        """
        call_stack = call_stack or set()
        types = set()
        types |= self.infer_type(node.left, call_stack=call_stack)
        types |= self.infer_type(node.right, call_stack=call_stack)
        return types

    def infer_tuple(self, node, call_stack=None):
        """
        Infer the contents of a tuple literal.
        """

        raise NotImplementedError

    def infer_type(self, node, call_stack=None):
        """
        Infer the type of an ast node.

        Will need to look in parent_env types.

        Args:
            node (ast node)

        Returns:
            set[Type]: All possible types that this expression could be
        """
        call_stack = call_stack or set()
        if isinstance(node, ast.Num):
            return self.infer_num(node)
        elif isinstance(node, ast.Str):
            return {self.__special_types["str"]}
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

    def parse_call(self, node):
        """
        Edit the function env to update the types of the arguments based
        on the types passed.

        Parse the arguments also
        """
        types = self.infer_type(node.func)
        for t in types:
            if isinstance(t, FunctionType):
                t.apply_call_args(node)
            elif isinstance(t, ClassType):
                # Call the __init__ method if provided
                # Then parse all other methods
                instance = next(iter(t.return_type()))
                inits = instance.get_attr("__init__")
                if inits:
                    init = next(iter(inits))  # FunctionType
                    init.apply_call_args(node)

        # Positional
        for arg in node.args:
            self.parse(arg)

        # Keyword
        for arg in node.keywords:
            self.parse(arg.value)

        # *args
        if node.starargs:
            self.parse(node.starargs)

        # **kwargs
        if node.kwargs:
            self.parse(node.kwargs)

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
                self.bind(target.id, value_types)
            elif isinstance(target, ast.Attribute):
                types = self.infer_type(target.value)
                for t in types:
                    t.add_attr(target.attr, value_types)

    def parse_sequence(self, nodes):
        for node in nodes:
            self.parse(node)

    def parse_func_def(self, node):
        """
        Create a new function type and add it to the env.
        """
        self.bind(node.name, {FunctionType(node, self, owner=self.__owner)})

    def parse_class_def(self, node):
        """
        Create a new class and instance type and add them to the env.
        """
        self.bind(node.name, {ClassType(node, self)})

    def parse_expr(self, node):
        """
        Will need to keep parsing expression to see if there are any function
        calls.
        """
        self.parse(node.value)

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
        elif isinstance(node, ast.Call):
            self.parse_call(node)
        elif isinstance(node, ast.Expr):
            self.parse_expr(node)
        elif isinstance(node, ast.ClassDef):
            self.parse_class_def(node)

    @classmethod
    def from_code(cls, code, **kwargs):
        return cls(init_node=ast.parse(code), **kwargs)

    def json(self, call_stack=None):
        """
        A json representation of this environment and nested envs for
        debugging purposes.
        """
        call_stack = call_stack or set()
        d = {}

        if self not in call_stack:
            call_stack.add(self)
            for var, types in self.variables().items():
                d[var] = [t.json(call_stack=call_stack) for t in types]

        return d

