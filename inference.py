# -*- coding: utf-8 -*-

import utils
import ast


class Type(object):
    def evaluate(self):
        """
        Return some delayed evaluation of what this type represents.

        The result must be hashable.
        """
        raise NotImplementedError

    def __str__(self):
        return str(self.evaluate())

    def __eq__(self, other):
        return self.evaluate() == other.evaluate()

    def __ne__(self, other):
        return not (self == other)

    def __hash__(self):
        return hash(self.evaluate())

    def clone(self):
        raise NotImplementedError


class BaseType(Type):
    def __init__(self, base_type: str) -> None:
        self.__base_type = base_type

    def evaluate(self):
        """
        Returns:
            str
        """
        return self.__base_type

    def clone(self):
        return BaseType(self.__base_type)


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
    def __init__(self, base_type=None):
        """
        Args:
            base_type (Type): Another type that this type is equivalent to.
        """
        if base_type is None:
            self.__types = []  # type: list[Type]
        elif isinstance(base_type, list):
            self.__types = base_type
        else:
            self.__types = [base_type]

    def evaluate(self):
        """
        Returns:
            frozenset[(str, Container, Mapping)]: Types of variables
        """
        if not self.__types:
            return "Any"
        elif len(self.__types) == 1:
            return self.__types[0].evaluate()

        types = set()
        for t in self.__types:
            if isinstance(t, MultiType):
                evaluated_t = t.evaluate()
                if isinstance(evaluated_t, frozenset):
                    # Merge any multitypes
                    types |= evaluated_t
                else:
                    types.add(evaluated_t)
            elif isinstance(t, (BaseType, Container, Mapping)):
                types.add(t.evaluate())
            else:
                raise RuntimeError("Unexpected type '{}'".format(type(t)))

        if "Any" in types:
            # Any type dominates the rest
            return "Any"

        return frozenset(types)

    def update(self, other: Type):
        """Update the types in this container."""
        self.__types.append(other)

    def replace(self, other):
        """Replace all types in this container with another list of types."""
        self.__types = other

    def clone(self):
        return MultiType([x for x in self.__types])


class Container(Type):
    def __init__(self, init_type:MultiType=None) -> None:
        self.__content = init_type or MultiType()

    def evaluate(self):
        """
        Returns:
            tuple[MultiType]: Tuple of size 1 with the only element
                representing the types of the contents.
        """
        return (self.__content.evaluate(), )

    def add(self, t):
        """Add a new type into the container."""
        self.__content.update(t)

    def clone(self):
        return Container(self.__content)


class Mapping(Type):
    def __init__(self, init_key_type:MultiType=None, init_val_type:MultiType=None):
        self.__key = init_key_type or MultiType()
        self.__val = init_val_type or MultiType()

    def evaluate(self):
        """
        Returns:
            tuple[MultiType]: Tuple of size 2 with the first element
                representing the key types and the second representing the
                value types.
        """
        return (self.__key.evaluate(), self.__val.evaluate())

    def add_key(self, key_type):
        self.__key.update(key_type)

    def add_val(self, val_type):
        self.__val.update(val_type)

    def clone(self):
        return Mapping(self.__key, self.__val)


class TypeInferer(object):
    def __init__(self, node, init_types=None):
        self.__global_env = init_types or {}
        self.__global_env = self.parse(node)

    @classmethod
    def from_code(cls, code, **kwargs):
        return cls(utils.generate_ast(code), **kwargs)

    def infer_list_type(self, lst, env):
        """
        Infer the contents of a list.
        """
        types = MultiType()
        for expr in lst.elts:
            types.update(self.infer_type(expr, env))
        return MultiType(Container(types))

    def infer_dict_type(self, d, env):
        """
        Infer the contents of a dictionary.
        """
        key_types = MultiType()
        for node in d.keys:
            key_types.update(self.infer_type(node, env))
        val_types = MultiType()
        for node in d.values:
            val_types.update(self.infer_type(node, env))
        return MultiType(Mapping(key_types, val_types))

    def infer_name(self, name, env):
        """
        Infer the type of a variable.
        """
        if name.id in env:
            return env[name.id]
        return MultiType(AnyType())

    def infer_unary_op(self, op, env):
        if isinstance(op.op, ast.Not):
            # If using Not, expression is always a boolean result
            return MultiType(BoolType())
        elif isinstance(op.op, ast.Invert):
            # Inversions only work on ints and bools and return only integers
            return MultiType(IntType())
        else:
            # Otherwise, the return value is either an int or float
            inferred = self.infer_type(op.operand, env).evaluate()
            t = MultiType()
            if "int" in inferred:
                t.update(IntType())
            if "float" in inferred:
                t.update(FloatType())
            return t

    def infer_binary_op(self, op, env):
        """
        This is tricky since these operations normally call magic methods
        which can be overriden in custom classes.

        TODO: Check if the type is builtin first. For now, the resulting types
        will just be either the resulting types of the left and right exprs.

        Returns:
            MultiType
        """
        left_t = self.infer_type(op.left, env).clone()
        left_t.update(self.infer_type(op.right, env))
        return left_t

    def infer_call(self, call, env):
        return self.infer_name(call.func.name, env)

    def infer_num(self, num, env):
        if isinstance(num.n, int):
            return MultiType(IntType())
        elif isinstance(num.n, float):
            return MultiType(FloatType())
        else:
            return MultiType(ComplexType())

    def infer_bool_op(self, expr, env):
        """
        Infer type of a boolean expression.
        The return type is whatever the result of any of these expressions are.

        x = var or call() or None
        """
        t = MultiType()
        for node in expr.values:
            t.update(self.infer_type(node, env).clone())
        return t

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
            MultiType
        """
        if isinstance(expr, ast.Num):
            return self.infer_num(expr, env)
        elif isinstance(expr, ast.Str):
            return MultiType(StrType())
        elif isinstance(expr, ast.Bytes):
            return MultiType(BytesType())
        elif isinstance(expr, (ast.List, ast.Tuple, ast.Set)):
            return self.infer_list_type(expr, env)
        elif isinstance(expr, ast.Dict):
            return self.infer_dict_type(expr, env)
        elif isinstance(expr, ast.NameConstant):
            if expr.value is None:
                return MultiType(NoneType())
            return MultiType(BoolType())
        elif isinstance(expr, ast.Name):
            return self.infer_name(expr, env)
        elif isinstance(expr, ast.Expr):
            return self.infer_type(expr.value, env)
        elif isinstance(expr, ast.UnaryOp):
            return self.infer_unary_op(expr, env)
        elif isinstance(expr, ast.BinOp):
            return self.infer_binary_op(expr, env)
        elif isinstance(expr, ast.BoolOp):
            return self.infer_bool_op(expr, env)
        elif isinstance(expr, ast.Compare):
            return MultiType(BoolType())
        elif isinstance(expr, ast.Call):
            return self.infer_call(expr, env)
        elif isinstance(expr, ast.Attribute):
            return self.infer_attr(expr)

        raise RuntimeError("Unable to determine type for expression '{}'".format(expr))

    def _update_env(self, env, var, t):
        """
        Update the type of a variable in an environment.

        Functions and classes contain nested environments.
        """
        if isinstance(t, MultiType):
            if var in env:
                env[var].update(t)
            else:
                env[var] = t
        elif isinstance(t, dict):
            if var in env:
                raise RuntimeError("Redefining variable '{}' with a function or class '{}'".format(var, t))
            env[var] = t
        else:
            raise RuntimeError(
                """All types added to the env must be another env or a
                MultiType. Unknown type '{}' was added.""".format(type(t)))

    def parse_assign(self, asgn, env):
        targets = asgn.targets
        value = asgn.value
        val_type = self.infer_type(value, env)

        for target in targets:
            # Handle ast.Names as targets for now.
            # TODO: Implement logic for assignment to other types (starred,
            # dicts, lists, etc.)
            if isinstance(target, ast.Tuple):
                for elem in target:
                    self._update_env(env, elem.id, val_type)
            else:
                self._update_env(env, target.id, val_type)
        return env

    def parse_aug_assign(self, aug_asgn, env):
        """
        The types will be the combination of the existing types and the type
        of what is being added.
        """
        self._update_env(env, aug_asgn.target.id,
                          self.infer_type(aug_asgn.value, env))
        return env

    def find_declared_vars(self, body):
        """
        Returns:
            list[str]: Variables defined in a body of statements
        """
        variables = []
        for node in body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        # Multiple variable assignment
                        variables.append(target.id)
                    elif isinstance(target, ast.Tuple):
                        # Handle unpacking of tuple
                        variables += [name.id for name in target.elts]
        return variables

    def _split_args(self, args, env):
        """
        Extract the positional, keyword, and vararg and kwarg args from an
        arguments node.

        Returns:
            list[str]: Positional args
            list[dict[str, Type]]: Keyword args and their types
            (None, str): vararg (*args). None if not provided.
            (None, str): kwarg (**kwargs). None if not provided.
        """
        if args.defaults:
            # To prevent indexing up to 0
            positional_args = [arg.arg for arg in args.args[:-len(args.defaults)]]
        else:
            positional_args = [arg.arg for arg in args.args]
        keyword_args = {}
        vararg = args.vararg.arg if args.vararg else None
        kwarg = args.kwarg.arg if args.kwarg else None

        # Regular keyword arguments
        # Defaults are the default values for the last len(args.defaults)
        # positional arguments
        for i, arg in enumerate(args.args[len(args.args) - len(args.defaults):]):
            keyword_args[arg.arg] = self.infer_type(args.defaults[i], env)

        # Keyword only arguments
        for i, arg in enumerate(args.kwonlyargs):
            if args.kw_defaults[i] is not None:
                keyword_args[arg.arg] = self.infer_type(args.kw_defaults[i], env)

        return positional_args, keyword_args, vararg, kwarg

    def find_global_vars(self, seq):
        """
        Find variables declared as global in a sequence of nodes.

        Returns:
            set[str]
        """
        return {name for node in seq if isinstance(node, ast.Global)
                for name in node.names}

    def find_nonlocal_vars(self, seq):
        """
        Find variables declared as nonlocal in a sequence of nodes.

        Returns:
            set[str]
        """
        return {name for node in seq if isinstance(node, ast.Nonlocal)
                for name in node.names}

    def infer_func_return_type(self, body, func_env):
        """
        Determine the function return type from the function body and
        environment.

        Returns:
            MultiType
        """
        ret_type = MultiType()
        found_type = False
        for node in body:
            if isinstance(node, ast.Return):
                ret_type.update(self.infer_type(node.value, func_env))
                found_type = True
        if not found_type:
            # Functions without a return return None by default
            return MultiType(NoneType())
        return ret_type

    def parse_func_def(self, func_def, env):
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
        """
        name = func_def.name

        # Create the new env to pass down
        func_env = {}
        func_env.update(env)

        # Find all variable definitions and remove them
        declared_vars = self.find_declared_vars(func_def.body)  # type: list[str]
        for var in declared_vars:
            func_env.pop(var, None)

        # Keep ones that are global/nonlocal
        global_vars = self.find_global_vars(func_def.body)  # type: list[str]
        for var in global_vars:
            func_env[var] = self.__global_env[var]
        nonlocal_vars = self.find_nonlocal_vars(func_def.body)
        for var in nonlocal_vars:
            func_env[var] = env[var]

        # Find and merge with arguments
        # Any *args or **kwargs arguments are dictionaries that can hold
        # any type.
        positional, keyword, vararg, kwarg = self._split_args(func_def.args, env)

        # Positional arguments will be no specified type for now
        for var in positional:
            func_env[var] = MultiType()

        # Keyword args have type already given
        func_env.update(keyword)

        # Vararg and kwarg are nothing for now
        if vararg:
            func_env[vararg] = Container()
        if kwarg:
            func_env[kwarg] = Mapping()

        func_env = self.parse_sequence(func_def.body, func_env)
        self._update_env(env, name, {
            "body": func_env,
            "return_type": self.infer_func_return_type(func_def.body, func_env)
        })

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
        env = env or self.__global_env
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
        types.update(env)
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

    def environment(self):
        return self.__global_env


