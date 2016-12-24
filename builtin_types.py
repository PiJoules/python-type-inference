# -*- coding: utf-8 -*-

import class_utils
import ast
import ast_utils


class Type(object):
    """
    All objects have a type and a callable return type.

    Example:
    x = 2
    # x has a type of int and no callable return type

    def func():
        return x
    # func has a type of function (that takes no args) and a callable return
    # type of int

    def func2():
        return func
    # func has a type of function (that takes no args) and a callable return
    # type of function (that also takes no args)
    """
    def __init__(self, init_attrs=None):
        # Mapping of str to MultiType
        # Use inline if expr to keep reference to a previously passed init_attrs
        self.__attrs = {} if init_attrs is None else init_attrs

    def type(self):
        """
        Return some delayed evaluation of what this type represents.

        The result must be hashable.

        Returns:
            some hashable representation of this type (str, tuple, etc.)
        """
        raise NotImplementedError

    def callable_return_type(self):
        """
        The type this type would return if it was called.

        This is called when an ast.Call node is found.

        Returns:
            MultiType
        """
        raise NotImplementedError

    def attrs(self):
        """
        This is the type that would be returned when an attribute in it is
        accessed.

        Used when received an ast.Attribute node.

        Returns:
            dict[str, MultiType]
        """
        return self.__attrs

    def get_attr(self, attr):
        return self.__attrs[attr]

    def merge_attrs(self, other):
        """
        Update types of attributes.

        Args:
            other (dict[str, MultiType])
        """
        for attr, val in other.items():
            self.add_attr(attr, val)

    def add_attr(self, attr, val):
        """
        Args:
            attr (str)
            val (MultiType)
        """
        attrs = self.__attrs
        if attr in attrs:
            attrs[attr].update(val)
        else:
            assert isinstance(val, MultiType)
            attrs[attr] = val

    def __str__(self):
        return str(self.type())

    def __eq__(self, other):
        return self.type() == other.type()

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.type())

    def clone(self):
        raise NotImplementedError("Clone not implemented for cls {}".format(type(self)))


class BaseType(Type):
    def __init__(self, base_type, init_attrs=None):
        super().__init__(init_attrs=init_attrs)
        self.__base_type = base_type

    def type(self):
        """
        Returns:
            str
        """
        return self.__base_type

    def clone(self):
        return BaseType(self.__base_type, init_attrs=self.attrs())


class AnyType(BaseType):
    def __init__(self):
        super().__init__("Any")


class BoolType(BaseType):
    def __init__(self):
        super().__init__("bool")


class IntType(BaseType):
    def __init__(self):
        super().__init__("int")


class FloatType(BaseType):
    def __init__(self):
        super().__init__("float")


class ComplexType(BaseType):
    def __init__(self):
        super().__init__("complex")


class StrType(BaseType):
    def __init__(self):
        super().__init__("str")


class BytesType(BaseType):
    def __init__(self):
        super().__init__("bytes")


class NoneType(BaseType):
    def __init__(self):
        super().__init__("None")


class MultiType(Type):
    """
    Class for performing delayed evaluation of types.
    This is a container of strings that is lazily evaluated.
    """
    def __init__(self, base_type=None, init_attrs=None):
        """
        Args:
            base_type (Type): Another type that this type is equivalent to.
        """
        super().__init__(init_attrs=init_attrs)
        if base_type is None:
            self.__types = []  # type: list[Type]
        elif isinstance(base_type, list):
            self.__types = base_type
        else:
            self.__types = [base_type]

    def empty(self):
        return bool(self.__types)

    #def attrs(self):
    #    raise NotImplementedError

    #def add_attr(self, attr, val):
    #    raise NotImplementedError

    #def get_attr(self, attr):
    #    raise NotImplementedError

    def type(self):
        """
        Returns:
            frozenset[(str, Container, Mapping)]: Types of variables
        """

        types = set()
        for t in self.__types:
            if isinstance(t, MultiType):
                evaluated_t = t.type()
                if isinstance(evaluated_t, frozenset):
                    # Merge any multitypes
                    types |= evaluated_t
                else:
                    types.add(evaluated_t)
            elif isinstance(t, Type):
                types.add(t.type())
            else:
                raise RuntimeError("Unexpected type '{}'".format(type(t)))

        if not types or "Any" in types:
            # Any type dominates the rest
            return "Any"

        if len(types) == 1:
            return types.pop()

        return frozenset(types)

    def update(self, other):
        """Update the types in this container."""
        if not isinstance(other, RecursionType):
            self.__types.append(other)

    def replace(self, other):
        """Replace all types in this container with another list of types."""
        self.__types = other

    def clone(self):
        return MultiType(list(self.__types), init_attrs=self.attrs())

    def contains(self, t):
        """Check if this type contains another type."""
        for other_t in self.__types:
            if isinstance(other_t, MultiType):
                return other_t.contains(t)
            elif other_t == t:
                return True
        return False


class RecursionType(MultiType):
    """
    A class meant to indicate that the callable return type of a function
    is dependent on the return type of the function itself.

    Example:
    def fib(n):
        if n < 2:
            return n
        return fib(n-1) + fib(n-2)

    In this example, the return type could be whatever the type of n is (which
    is Any for now until backtracking function calls shows more about the type)
    or whatever the return values for fib(n-1) and fib(n-2) are.
    Determining the return values of these recursive calls requires knowing
    the return value of the functions again which could go on forever when
    really the return value should just be tied to whatever the type of n is.

    This will be aleviated by having this type return an empty set as its type()
    and having this be the return type for calls to functions that call
    themselves. This will allow for any MultiTypes that have these added to it
    treat these as empty sets.
    """

    def type(self):
        return frozenset()

    def clone(self):
        return RecursionType()


class Container(Type):
    def __init__(self, init_type=None, init_attrs=None):
        super().__init__(init_attrs=init_attrs)
        self.__content = init_type or MultiType()

    def type(self):
        """
        Returns:
            tuple[MultiType]: Tuple of size 1 with the only element
                representing the types of the contents.
        """
        return (self.__content.type(), )

    def add(self, t):
        """Add a new type into the container."""
        self.__content.update(t)

    def clone(self):
        return Container(self.__content, init_attrs=self.attrs())

    def content(self):
        return self.__content


class Mapping(Type):
    def __init__(self, init_key_type=None, init_val_type=None,
                 init_attrs=None):
        super().__init__(init_attrs=init_attrs)
        self.__key = init_key_type or MultiType()
        self.__val = init_val_type or MultiType()

    def type(self):
        """
        Returns:
            tuple[MultiType]: Tuple of size 2 with the first element
                representing the key types and the second representing the
                value types.
        """
        return (self.__key.type(), self.__val.type())

    def add_key(self, key_type):
        self.__key.update(key_type)

    def add_val(self, val_type):
        self.__val.update(val_type)

    def clone(self):
        return Mapping(self.__key, self.__val, init_attrs=self.attrs())

    def key(self):
        return self.__key

    def value(self):
        return self.__val


class ArgumentsInfo(class_utils.SlotDefinedClass):
    __slots__ = ("positional", "keyword", "vararg", "keyword_only", "kwarg",
                 "keyword_defaults", "keyword_only_defaults", "is_method",
                 "cls_info")
    __types__ = {
        "positional": [str],
        "keyword": {str: MultiType},
        "vararg": class_utils.optional(str),
        "keyword_only": {str: class_utils.optional(MultiType)},
        "kwarg": class_utils.optional(str),
        "is_method": bool,
    }

    __defaults__ = {
        "vararg": None,
        "kwarg": None,
        "is_method": False,
        "cls_info": None,
    }

    def environment(self):
        """
        Treat the arguments as an environment and return it.

        Returns:
            dict
        """
        func_env = {}

        if self.is_method:
            start = 1
            func_env[self.positional[0]] = MultiType(BaseType(self.cls_info.name))
        else:
            start = 0
        for var in self.positional[start:]:
            func_env[var] = MultiType()

        # Keyword args have type already given
        func_env.update(self.keyword)
        func_env.update(self.keyword_only)

        # Vararg and kwarg are nothing for now
        if self.vararg:
            func_env[self.vararg] = MultiType(Container())
        if self.kwarg:
            func_env[self.kwarg] = MultiType(Mapping())

        return func_env

    @classmethod
    def from_arguments_node(cls, args, inferer, is_method=False, cls_info=None):
        """
        Extract the positional, keyword, and vararg and kwarg args from an
        arguments node.
        """
        if args.defaults:
            # To prevent indexing up to 0
            positional_args = [arg.arg for arg in args.args[:-len(args.defaults)]]
        else:
            positional_args = [arg.arg for arg in args.args]
        keyword_args = {}
        keyword_defaults = {}  # maps str to ast node
        keyword_only_args = {}
        keyword_only_defaults = {}
        vararg = args.vararg.arg if args.vararg else None
        kwarg = args.kwarg.arg if args.kwarg else None

        # Regular keyword arguments
        # Defaults are the default values for the last len(args.defaults)
        # positional arguments
        for i, arg in enumerate(args.args[len(args.args) - len(args.defaults):]):
            keyword_args[arg.arg] = inferer.infer_type(args.defaults[i])
            keyword_defaults[arg.arg] = args.defaults[i]

        # Keyword only arguments
        for i, arg in enumerate(args.kwonlyargs):
            if args.kw_defaults[i] is not None:
                keyword_only_args[arg.arg] = inferer.infer_type(args.kw_defaults[i])
            else:
                # This required keyword argument has no default type
                keyword_only_args[arg.arg] = MultiType(AnyType())
            keyword_only_defaults[arg.arg] = args.kw_defaults[i]

        return cls(
            positional=positional_args,
            keyword=keyword_args,
            vararg=vararg,
            keyword_only=keyword_only_args,
            kwarg=kwarg,
            keyword_defaults=keyword_defaults,
            keyword_only_defaults=keyword_only_defaults,
            is_method=is_method,
            cls_info=cls_info
        )


class CallableType(Type):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def name(self):
        raise NotImplementedError

    def environment(self):
        raise NotImplementedError


class FunctionType(CallableType):
    def __init__(self, func_def, inferer, is_method=False, owner=None,
                 global_inferer=None, init_attrs=None):
        """
        This function will contain its own inferer that will be extended
        to contain variables declared in this function body.

        1. Parse arguments.
        2. Clone outer inferer env.
        """
        super().__init__(init_attrs=init_attrs)
        self.__func_def = func_def
        self.__name = func_def.name
        self.__inferer = inferer
        self.__global_inferer = global_inferer or inferer
        self.__is_method = is_method
        self.__owner = owner

        # Clone
        self.__inferer = inferer.clone()
        self.__envionment = None
        self.__return_type = None

    def clone(self):
        return FunctionType(
            self.__func_def, self.__inferer, is_method=self.__is_method,
            owner=self.__owner, global_inferer=self.__global_inferer,
            init_attrs=self.attrs()
        )

    def name(self):
        return self.__name

    def inferer(self):
        """
        The inferer environment contains the arguments and the function itself.
        """
        return self.__inferer

    def type(self):
        return "function"

    def arguments(self):
        return ArgumentsInfo.from_arguments_node(
            self.__func_def.args, self.__inferer, is_method=self.__is_method,
            cls_info=self.__owner)

    def environment(self):
        """
        Will need to account for globals and nonlocals.

        Variables declared outside the scope of the function body will be
        carried into the body with the same types. A variable type will be
        replaced inside this new environment if it is declared inside the
        function body or given as a function argument. If the variable
        defined in the function is global or nonlocal, the types in the
        respective upper environments are carried down still and can be
        updated.

        1. Parse function body initially for assignments of variables
           declared in the env passed down.
        2. Parse function body for global/nonlocal declared variables.
        3. Remove variables from the env that are declared in the function
           body, but keeping ones that are global/nonlocal in the func body.
           The new types of global variables are the types in the global scope,
           and the types on nonlocal ones are the types passed from the
           previous env.

        TODO: Handle decorators, especially, @classmethod, @property, and @staticmethod

        Args:
            func_def (ast.FunctionDef)
            env (dict)
            is_method (bool): Flag indicating the current function is an object method.
            cls_info (types.ClassType): The type of the first argument in this method if
                is_method is True
        """
        if self.__envionment is None:
            inferer = self.__inferer
            func_def = self.__func_def
            is_method = self.__is_method
            owner = self.__owner
            global_inferer = self.__global_inferer

            # Create new env to pass down
            func_env = {}
            func_env.update(inferer.environment())

            # Add class type to environment if provided
            if is_method:
                inferer.update_env(owner.name, owner, func_env)

            # Self was already added to inferer in the parse_func_def func

            # Find all variable definitions and remove them
            declared_vars = inferer.find_declared_vars(func_def.body)  # type: list[str]
            for var in declared_vars:
                func_env.pop(var, None)

            # Keep ones that are global
            # TODO: Add logic for handling nonlocal vars
            global_vars = inferer.find_global_vars(func_def.body)  # type: list[str]
            for var in global_vars:
                func_env[var] = global_inferer.environment()[var]

            # Merge args
            func_env.update(self.arguments().environment())

            # The func env passed to this contains the arguments and the function
            # itself
            func_env = inferer.parse_sequence(func_def.body, func_env)
            #return func_env
            self.__envionment = func_env
        return self.__envionment

    def callable_return_type(self):
        if self.__return_type is None:
            func_env = self.environment()
            inferer = self.__inferer

            ret_type = MultiType()
            found_type = False

            stack = list(self.__func_def.body)
            while stack:
                node = stack.pop()
                if isinstance(node, ast.Return):
                    print("node val:", node.value)
                    t = inferer.infer_type(node.value, func_env)
                    print("found type:", type(t), t)
                    ret_type.update(t)
                    found_type = True
                elif isinstance(node, (ast.If, ast.While, ast.For)):
                    stack += node.body + node.orelse
                elif isinstance(node, ast.Try):
                    stack += node.body + node.orelse + node.finalbody
                    for handler in node.handlers:
                        stack += handler.body
                elif isinstance(node, ast.With):
                    stack += node.body

            if not found_type:
                # Functions without a return return None by default
                ret_type = MultiType(NoneType())
            #return ret_type
            self.__return_type = ret_type
        print("callable_return_type:", self.name(), self.__return_type)
        return self.__return_type


class ClassType(CallableType):
    def __init__(self, cls_def, inferer, global_inferer=None,
                 init_attrs=None):
        super().__init__(init_attrs=init_attrs)
        self.__name = cls_def.name
        self.__cls_def = cls_def
        self.__inferer = inferer
        self.__global_inferer = global_inferer or inferer

    def clone(self):
        return ClassType(self.__cls_def, self.__inferer,
                         global_inferer=self.__global_inferer,
                         init_attrs=self.attrs())

    def type(self):
        return "type"

    def instance_name(self):
        return self.__name + "_instance"

    def callable_return_type(self):
        """
        All instances will point to the same type so that changes in
        attributes that affect one instance will affect all instances.
        """
        env = self.__inferer.environment()

        name = self.instance_name()

        if name not in env:
            instance = MultiType(
                InstanceType(
                    self.__cls_def, self.__inferer,
                    global_inferer=self.__global_inferer,
                    init_attrs=self.attrs(),
                )
            )
            env[name] = instance
        return env[name]

    def name(self):
        return self.__name

    def attrs(self):
        """
        It is simpler to just think of a class as a namespace or a module.
        All attributes can be treated and access normally as if the class
        itself was another module by calling my_class.attr. All varibales
        in the higher level env are brought and copied into this class' env.

        Returns:
            dict[str, Type]: Mapping of string to functions
        """
        return self.environment()

    def environment(self):
        """
        Rules for the environment available are analagous to a function that
        does not have any arguments, and only the class itself is added to the
        nested env.

        Will also need to parse parents for values.
        """
        inferer = self.__inferer
        cls_def = self.__cls_def
        global_inferer = self.__global_inferer

        # Create new env to pass down
        cls_env = {}
        cls_env.update(inferer.environment())

        # Class was already added to inferer in the parse_class_def func

        # The func env passed to this contains the arguments and the function
        # itself
        cls_env = inferer.parse_sequence(cls_def.body, cls_env)
        return cls_env


class InstanceType(CallableType):
    def __init__(self, cls_def, inferer, global_inferer=None,
                 init_attrs=None):
        super().__init__(init_attrs=init_attrs)
        self.__name = cls_def.name
        self.__cls_def = cls_def
        self.__inferer = inferer
        self.__global_inferer = global_inferer or inferer

    def clone(self):
        return InstanceType(self.__cls_def, self.__inferer,
                            global_inferer=self.__global_inferer,
                            init_attrs=self.attrs())

    def type(self):
        return self.__name

    def callable_return_type(self):
        raise NotImplementedError

    def name(self):
        return self.__name

    def attrs(self):
        """
        The attributes include all class attributes and ones set by self.___ = ...
        Class attributes can be accessed with self., but can be overrided by
        setting that attribute to another value somewhere. This requires
        asjusting the parse_assign method to allowing setting of attributes.

        Rules for handling functions and types in an instance as similar
        to those handled in a class, but the default attributes in a class
        are copied and propagated down to an instance. Changing an overwritten
        instance type does not change a class type.

        Methods in a class are also available to an instance, but during calls,
        the first argument is automatically set to this instance type and any
        calls to a method of an instance require all but th first argument in
        the definition to be provided.

        Example:
        Calling obj.method(arg1) expands to obj.method(obj, arg1) where the
        first argument in the obj.method represents the self.

        Returns:
            dict[str, Type]: Mapping of string to functions
        """
        inferer = self.__inferer
        cls_def = self.__cls_def
        global_inferer = self.__global_inferer

        # Create new env to pass down
        cls_env = {}
        cls_env.update(inferer.environment())

        # Class was already added to inferer in the parse_class_def func

        # The func env passed to this contains the arguments and the function
        # itself
        cls_env = inferer.parse_sequence(cls_def.body, cls_env)
        return cls_env

    def environment(self):
        return self.attrs()


