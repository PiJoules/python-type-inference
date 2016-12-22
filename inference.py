# -*- coding: utf-8 -*-

import ast_utils
import class_utils
import builtin_types as types
import ast


class ArgumentsInfo(class_utils.SlotDefinedClass):
    __slots__ = ("positional", "keyword", "vararg", "keyword_only", "kwarg",
                 "keyword_defaults", "keyword_only_defaults", "is_method",
                 "cls_info")
    __types__ = {
        "positional": [str],
        "keyword": {str: types.MultiType},
        "vararg": class_utils.optional(str),
        "keyword_only": {str: class_utils.optional(types.MultiType)},
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
            func_env[self.positional[0]] = BaseType(self.cls_info.name)
        else:
            start = 0
        for var in self.positional[start:]:
            func_env[var] = types.MultiType()

        # Keyword args have type already given
        func_env.update(self.keyword)
        func_env.update(self.keyword_only)

        # Vararg and kwarg are nothing for now
        if self.vararg:
            func_env[self.vararg] = types.Container()
        if self.kwarg:
            func_env[self.kwarg] = types.Mapping()

        return func_env


class FunctionInfo(class_utils.SlotDefinedClass):
    __slots__ = ("name", "body_env", "return_type", "arguments", "returns_class",
                 "class_info")
    __types__ = {
        "name": str,
        "body_env": dict,
        "return_type": types.MultiType,
        "arguments": ArgumentsInfo,
        "returns_class": bool,
    }

    __defaults__ = {
        "returns_class": False,
        "class_info": None
    }


class ClassInfo(class_utils.SlotDefinedClass):
    __slots__ = ("name", "parents", "methods", "classes", "class_properties", "constructor",
                 "object_properties")
    __types__ = {
        "name": str,
        "parents": [types.MultiType],
        "methods": {str: FunctionInfo},
        "classes": dict,  # Nested classes; available to class and instance
        "class_properties": {str: types.MultiType},  # Avaialble to the class and instance
        "object_properties": {str: types.MultiType},  # Available to the instance only
        "constructor": FunctionInfo,
    }


class TypeInferer(object):
    def __init__(self, node, init_types=None):
        self.__global_env = init_types or {}
        self.__global_env = self.parse_module(node, self.__global_env)

    @classmethod
    def from_code(cls, code, **kwargs):
        return cls(ast_utils.generate_ast(code), **kwargs)

    def infer_list_type(self, lst, env):
        """
        Infer the contents of a list.
        """
        contents = types.MultiType()
        for expr in lst.elts:
            contents.update(self.infer_type(expr, env))
        return types.MultiType(types.Container(contents))

    def infer_dict_type(self, d, env):
        """
        Infer the contents of a dictionary.
        """
        key_types = types.MultiType()
        for node in d.keys:
            key_types.update(self.infer_type(node, env))
        val_types = types.MultiType()
        for node in d.values:
            val_types.update(self.infer_type(node, env))
        return types.MultiType(types.Mapping(key_types, val_types))

    def infer_name(self, name, env):
        """
        Infer the type of a variable.
        """
        if name.id in env:
            return env[name.id]
        raise RuntimeError("Variable '{}' not previously declared in scope.".format(name.id))

    def infer_unary_op(self, op, env):
        if isinstance(op.op, ast.Not):
            # If using Not, expression is always a boolean result
            return types.MultiType(types.BoolType())
        elif isinstance(op.op, ast.Invert):
            # Inversions only work on ints and bools and return only integers
            return types.MultiType(types.IntType())
        else:
            # Otherwise, the return value is either an int or float
            inferred = self.infer_type(op.operand, env).evaluate()
            t = types.MultiType()
            if "int" in inferred:
                t.update(types.IntType())
            if "float" in inferred:
                t.update(types.FloatType())
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

    def determine_expr_name(self, expr):
        """
        Find the name of an expression. This essentially only works on names,
        attributes
        """
        pass

    def infer_call(self, call, env):
        #return self.infer_name(call.func.name, env)
        raise NotImplementedError

    def infer_num(self, num, env):
        if isinstance(num.n, int):
            return types.MultiType(types.IntType())
        elif isinstance(num.n, float):
            return types.MultiType(types.FloatType())
        else:
            return types.MultiType(types.ComplexType())

    def infer_bool_op(self, expr, env):
        """
        Infer type of a boolean expression.
        The return type is whatever the result of any of these expressions are.

        x = var or call() or None
        """
        t = types.MultiType()
        for node in expr.values:
            t.update(self.infer_type(node, env).clone())
        return t

    def infer_attr(self, attr, env):
        """
        Will need to initially have performed a search for determining
        attribute type on an object.
        """
        return self.parse(attr.value, env)[attr.attr]

    def infer_type(self, expr, env):
        """
        Infer the types of a variable

        Returns:
            MultiType
        """
        if isinstance(expr, ast.Num):
            return self.infer_num(expr, env)
        elif isinstance(expr, ast.Str):
            return types.MultiType(types.StrType())
        elif isinstance(expr, ast.Bytes):
            return types.MultiType(types.BytesType())
        elif isinstance(expr, (ast.List, ast.Tuple, ast.Set)):
            return self.infer_list_type(expr, env)
        elif isinstance(expr, ast.Dict):
            return self.infer_dict_type(expr, env)
        elif isinstance(expr, ast.NameConstant):
            if expr.value is None:
                return types.MultiType(types.NoneType())
            return types.MultiType(types.BoolType())
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
            return types.MultiType(types.BoolType())
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
        if isinstance(t, types.MultiType):
            if var in env:
                env[var].update(t)
            else:
                env[var] = t
        elif isinstance(t, (ClassInfo, FunctionInfo)):
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

    def create_arguments_info(self, args, env, is_method=False, cls_info=None):
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
            keyword_args[arg.arg] = self.infer_type(args.defaults[i], env)
            keyword_defaults[arg.arg] = args.defaults[i]

        # Keyword only arguments
        for i, arg in enumerate(args.kwonlyargs):
            if args.kw_defaults[i] is not None:
                keyword_only_args[arg.arg] = self.infer_type(args.kw_defaults[i], env)
            else:
                # This required keyword argument has no default type
                keyword_only_args[arg.arg] = types.MultiType(types.AnyType())
            keyword_only_defaults[arg.arg] = args.kw_defaults[i]

        return ArgumentsInfo(
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
        ret_type = types.MultiType()
        found_type = False
        for node in body:
            if isinstance(node, ast.Return):
                ret_type.update(self.infer_type(node.value, func_env))
                found_type = True
        if not found_type:
            # Functions without a return return None by default
            return types.MultiType(types.NoneType())
        return ret_type

    def parse_func_def(self, func_def, env, is_method=False, cls_info=None):
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
            cls_info (ClassInfo): The type of the first argument in this method if
                is_method is True
        """
        name = func_def.name

        # Create the new env to pass down
        func_env = {}
        func_env.update(env)

        # Add the class type to the environment
        if is_method:
            self._update_env(func_env, cls_info.name, cls_info)

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
        args_info = self.create_arguments_info(func_def.args, env, is_method=is_method,
                                               cls_info=cls_info)

        func_env.update(args_info.environment())

        func_env = self.parse_sequence(func_def.body, func_env)

        func_info = FunctionInfo(
            name=name,
            body_env=func_env,
            return_type=self.infer_func_return_type(func_def.body, func_env),
            arguments=args_info,
        )

        self._update_env(env, name, func_info)

        return env

    def parse_class_def(self, cls_def, env):
        """
        Same rules as function, but will contain nested functions.

        TODO: Handle decorators and keyword arguments in parents
        """
        name = cls_def.name

        parents = [self.infer_type(base, env) for base in cls_def.bases]

        cls_body = cls_def.body
        cls_env = {}
        cls_env.update(env)

        # This class itself is not availble in the body of its definition,
        # but it is available in the methods.
        cls_type = BaseType(name)
        cls_env.update(self.parse_sequence(cls_body, cls_env, is_cls_body=True,
                                           cls_info=cls_type))

        return env

    def parse(self, node, env=None, is_cls_body=False, cls_info=None):
        """
        Wrapper for parsing all misceanious nodes.

        Args:
            node (ast.AST)
            env (dict)
            is_cls_body (bool): Flag indicating this statement is inside a class definition
            cls_info (BaseType): The type of this object if inside a class definition body

        Returns:
            dict
        """
        env = env or self.__global_env
        if isinstance(node, ast.Assign):
            return self.parse_assign(node, env)
        elif isinstance(node, ast.AugAssign):
            return self.parse_aug_assign(node, env)
        elif isinstance(node, ast.FunctionDef):
            return self.parse_func_def(node, env, is_method=is_cls_body,
                                       cls_info=cls_info)
        elif isinstance(node, ast.ClassDef):
            return self.parse_class_def(node, env)
        return {}

    def parse_sequence(self, seq, env, is_cls_body=False, cls_info=None):
        """
        Parse nodes in a sequence of nodes.

        Args:
            seq (list[ast.AST])
            env (dict)
            is_cls_body (bool): Flag indicating this statement is inside a class definition
            cls_info (BaseType): The type of this object if inside a class definition body

        Returns:
            dict
        """
        contents = {}
        contents.update(env)
        for node in seq:
            contents.update(self.parse(node, env, is_cls_body=is_cls_body,
                                       cls_info=cls_info))
        return contents

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


