# -*- coding: utf-8 -*-

import ast
import astor


def simple(collection):
    if len(collection) == 1:
        return next(iter(collection))
    return collection


def hash_node(node):
    return hash(astor.to_source(node))


class Object:
    def __init__(self):
        self.__attrs = {}

    def attrs(self):
        """
        Returns:
            dict[str, set[Object]]
        """
        return self.__attrs

    def get_attr(self, attr):
        return self.__attrs.get(attr, None)

    def add_attr(self, attr, val):
        assert isinstance(val, set)
        assert all(isinstance(x, Object) for x in val)

        if attr in self.__attrs:
            self.__attrs[attr] |= val
        else:
            self.__attrs[attr] = val

    def __eq__(self, other):
        #return isinstance(other, Object) and isinstance(self, type(other))
        #return type(self) == type(other)
        return hash(self) == hash(other)

    def __hash__(self):
        """The hash just needs to be able to distinct between different types."""
        raise NotImplementedError


class BaseObject(Object):
    def __init__(self, name):
        super().__init__()
        self.__name = name

    def __hash__(self):
        return hash(self.__name)


class IntObject(BaseObject):
    def __init__(self):
        super().__init__("int")

class FloatObject(BaseObject):
    def __init__(self):
        super().__init__("float")

class ComplexObject(BaseObject):
    def __init__(self):
        super().__init__("complex")

class StringObject(BaseObject):
    def __init__(self):
        super().__init__("str")

class ComplexObject(BaseObject):
    def __init__(self):
        super().__init__("complex")

class AnyObject(BaseObject):
    def __init__(self):
        super().__init__("Any")

class NoneObject(BaseObject):
    def __init__(self):
        super().__init__("None")


class TupleObject(Object):
    def __init__(self):
        super().__init__()

    def __hash__(self):
        raise NotImplementedError


class ContainerObject(Object):
    def __init__(self, init_contents=None):
        super().__init__()
        self.__contents = init_contents or []

    def content_types(self):
        if self.__contents:
            return set(self.__contents)
        else:
            return {AnyObject()}

    def __hash__(self):
        """
        Need to be able to differenciate between other types and other lists
        containing different types.
        """
        return hash(frozenset(self.__contents))


class DictObject(Object):
    def __init__(self, init_keys=None, init_vals=None):
        super().__init__()
        self.__keys = init_keys or []
        self.__vals = init_vals or []

    def key_types(self):
        if self.__keys:
            return set(self.__keys)
        else:
            return {AnyObject()}

    def value_types(self):
        if self.__vals:
            return set(self.__vals)
        else:
            return {AnyObject()}

    def __hash__(self):
        return hash((frozenset(self.__keys), frozenset(self.__vals)))


class ClassObject(Object):
    def __init__(self, node, env):
        """
        All variables assigned in this env are attributes of this type and
        its instance.
        """
        super().__init__()
        self.__node = node
        self.__env = env

        # This env should not persist outside this function. It is only used
        # for finding the attributes of this class.
        new_env = Environment.from_env(env)
        new_env.parse_sequence(node.body)
        for var, types in new_env.variables().items():
            self.add_attr(var, types)

    def return_type(self, call_stack=None):
        return {InstanceObject(self.__node, self.__env)}

    def __hash__(self):
        return hash(self.__node.name)


class ClassObjectMock(ClassObject):
    def __init__(self, name):
        self.__name = name

    def __hash__(self):
        return hash(self.__name)


class InstanceObject(Object):
    def __init__(self, node, env):
        """
        Create an instance from a class.

        The methods are automatically parsed on the FunctionType creation in
        the environment parse.
        """
        super().__init__()
        self.__node = node

        new_env = Environment.from_env(env, owner=self)
        new_env.parse_sequence(node.body)
        for var, types in new_env.variables().items():
            self.add_attr(var, types)

    def name(self):
        return self.__node.name + "___instance"

    def __hash__(self):
        # TODO: Find a better way to hash instances
        return hash(self.name())


class InstanceObjectMock(InstanceObject):
    def __init__(self, name):
        self.__name = name

    def __hash__(self):
        return hash(self.__name + "___instance")


class FunctionObject(Object):
    def __init__(self, node, env, owner=None):
        super().__init__()

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
            args_dict[arg.arg] = env.infer_expr(args_node.defaults[i])

        self.__positional = [a.arg for a in pos_args[start:]]  # list[str]

        # Keyword args
        keyword_args = args_node.kwonlyargs
        defaults = args_node.kw_defaults
        for i, kwarg in enumerate(keyword_args):
            if defaults[i] is None:
                args_dict[kwarg.arg] = set()
            else:
                args_dict[kwarg.arg] = env.infer_expr(defaults[i])

        # Vararg and kwargs
        if args_node.vararg:
            args_dict[args_node.vararg.arg] = {ContainerObject()}
        if args_node.kwarg:
            args_dict[args_node.kwarg.arg] = {DictObject()}

        # Checks on the args_dict
        for k, v in args_dict.items():
            assert isinstance(k, str)
            assert isinstance(v, set)
            assert all(isinstance(t, Object) for t in v)

        # Function envs are parsed on creation
        func_env = Environment.from_env(env, init_variables=args_dict)
        func_env.parse_sequence(node.body)
        self.__env = func_env

    def return_type(self, call_stack=None):
        call_stack = call_stack or set()
        env = self.__env

        types = set()

        # Find all return statements
        # Use boolean instead of checking empty types because infer_expr()
        # could return an empty set
        found_type = False
        stack = list(self.__node.body)
        while stack:
            node = stack.pop()
            if isinstance(node, ast.Return):
                types = env.infer_expr(node.value, call_stack=call_stack)
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
        assert all(isinstance(t, Object) for t in types)

        if not found_type:
            return {NoneObject()}

        return types

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
            env.bind(self.__positional[i], env.infer_expr(arg))

        # Apply keyword
        for kwarg in node.keywords:
            env.bind(kwarg.arg, env.infer_expr(kwarg.value))

        # Re-evaluate the body
        env.parse_sequence(self.__node.body)

    def environment(self):
        return self.__env

    def __hash__(self):
        """
        Functions are user defined at runtime, so all functions will be
        different.
        """
        return hash(self.__node.name)


class FunctionObjectMock(FunctionObject):
    def __init__(self, name):
        self.__name = name

    def __hash__(self):
        return hash(self.__name)


class Environment:
    def __init__(self, parent_env=None, owner=None, init_variables=None):
        self.__variables = init_variables or {}
        self.__parent_env = parent_env
        self.__child_envs = []
        self.__owner = owner
        self.__types = {}

    @classmethod
    def from_env(cls, env, **kwargs):
        new_env = cls(
            parent_env=env,
            **kwargs
        )
        env.add_child_env(new_env)
        return new_env

    def add_child_env(self, env):
        self.__child_envs.append(env)

    def child_envs(self):
        return self.__child_envs

    def types(self):
        return self.__types

    def accumulate_types(self):
        """
        For each type used in this env, gatther all of the attribute types.

        Be sure to check nested envs for objects that add attributes to
        types in the current env.

        Returns:
            dict[Object, dict[str, set[Object]]]


        types = self.infer_expr(node.func)
        for t in types:
            if isinstance(t, FunctionObject):
                t.apply_call_args(node)
            elif isinstance(t, ClassObject):
                print(t)
                # Call the __init__ method if provided
                # Then parse all other methods
                instance = next(iter(t.return_type()))
                inits = instance.get_attr("__init__")
                print("inits:", inits)
                if inits:
                    init = next(iter(inits))  # FunctionObject
                    init.apply_call_args(node)
                    print(next(iter(init.environment().variables()["self"])).attrs())
        """
        types = {}
        #print("self:", id(self))

        # Check own variables
        for objs in self.__variables.values():
            for obj in objs:
                #print("self:", obj.attrs(), obj not in types)
                #if isinstance(obj, InstanceObject):
                #    #print("types:", {hash(x):x for x in types})
                #    print(obj.name(), hash(obj))
                if obj not in types:
                    types[obj] = dict(obj.attrs())  # dict[str, set[Object]]
                else:
                    for attr, vals in obj.attrs().items():
                        types[obj][attr] |= vals
                        #if attr == "_a":
                        #    print(attr, vals)

        #print("types:", {hash(x): type(x) for x in types})
        #print("halfway")

        #print("children:", [id(x) for x in self.__child_envs])
        # Check children to see if they added attributes
        child_envs = list(self.__child_envs)
        #for child_env in self.__child_envs:
        while child_envs:
            child_env = child_envs.pop()
            child_envs += child_env.child_envs()  # Add rest

            child_types = child_env.accumulate_types()
            #print("child_types:", [type(x) for x in child_types])
            for obj, attrs in child_types.items():
                #print(obj, obj in types, hash(obj))
                #print("child:", attrs, obj, obj in types)
                #if isinstance(obj, InstanceObject):
                #    print(obj.name(), hash(obj), [type(x) for x in types], obj in types)
                if obj in types:
                    #if isinstance(obj, InstanceObject):
                    #    print("OBJ IN TYPE")
                    # Merge any attributes for this object
                    for attr, vals in attrs.items():
                        types[obj][attr] |= vals
                        #if attr == "_a":
                        #    print(attr, vals)

        #print("final:", [type(x) for x in types])
        return types

    def json_types(self):
        types = {}
        for objs in self.__variables.values():
            for obj in objs:
                if obj not in types:
                    types[obj] = dict(obj.attrs())  # dict[str, set[Object]]
                else:
                    for attr, vals in obj.attrs().items():
                        types[obj][attr] |= vals
        return types

    def parse_sequence(self, seq):
        for node in seq:
            self.parse(node)

    def parse_module(self, node):
        self.parse_sequence(node.body)
        self.__types = self.accumulate_types()

    def bind(self, var, objects):
        assert isinstance(objects, set)
        assert all(isinstance(x, Object) for x in objects)

        if var in self.__variables:
            self.__variables[var] |= objects
        else:
            self.__variables[var] = objects

    def infer_num(self, node):
        n = node.n
        if isinstance(n, int):
            return IntObject()
        elif isinstance(n, float):
            return FloatObject()
        elif isinstance(n, complex):
            return ComplexObject()
        else:
            raise RuntimeError("Unknown num type {}".format(n))

    def infer_name(self, node):
        if node.id in self.__variables:
            return set(self.__variables[node.id])
        raise RuntimeError("Variable {} not declared in scope prior.".format(node.id))

    def infer_call(self, node, call_stack=None):
        self.parse_call(node)
        call_stack = call_stack or set()
        ret_types = set()

        if node not in call_stack:
            call_stack.add(node)
            types = self.infer_expr(node.func, call_stack=call_stack)
            for t in types:
                if isinstance(t, (FunctionObject, ClassObject)):
                    ret_types |= t.return_type(call_stack=call_stack)

        return ret_types

    def infer_attribute(self, node, call_stack=None):
        value = node.value  # ast node
        attr = node.attr  # str
        attr_types = set()
        call_stack = call_stack or set()
        value_types = self.infer_expr(value, call_stack=call_stack)

        for t in value_types:
            attr_type = t.get_attr(attr)
            if attr_type is not None:
                attr_types |= attr_type

        return attr_types

    def infer_expr(self, node, call_stack=None):
        """
        Create objects from a node.

        Returns:
            set[Object]
        """
        call_stack = call_stack or set()
        if isinstance(node, ast.Num):
            return {self.infer_num(node)}
        elif isinstance(node, ast.Name):
            return self.infer_name(node)
        elif isinstance(node, ast.Call):
            return self.infer_call(node)
        elif isinstance(node, ast.Str):
            return {StringObject()}
        elif isinstance(node, ast.Attribute):
            return self.infer_attribute(node)
        else:
            raise NotImplementedError("No logic yet implemented for infering node {}".format(node))

    def parse_call(self, node):
        types = self.infer_expr(node.func)
        for t in types:
            if isinstance(t, FunctionObject):
                t.apply_call_args(node)
            elif isinstance(t, ClassObject):
                #print(t)
                # Call the __init__ method if provided
                # Then parse all other methods
                instance = next(iter(t.return_type()))
                inits = instance.get_attr("__init__")
                #print("inits:", inits)
                if inits:
                    init = next(iter(inits))  # FunctionObject
                    init.apply_call_args(node)
                    #print(next(iter(init.environment().variables()["self"])).attrs())

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
        targets = node.targets
        value = node.value
        value_types = self.infer_expr(value)

        for target in targets:
            if isinstance(target, ast.Name):
                self.bind(target.id, value_types)
            elif isinstance(target, ast.Attribute):
                types = self.infer_expr(target.value)
                for t in types:
                    t.add_attr(target.attr, value_types)
            else:
                raise NotImplementedError("No logic implemented for assigning to target node {}".format(target))

    def parse_func_def(self, node):
        self.bind(
            node.name,
            {FunctionObject(node, self, owner=self.__owner)}
        )

    def parse_class_def(self, node):
        self.bind(
            node.name,
            {ClassObject(node, self)}
        )

    def parse(self, node):
        if isinstance(node, ast.Module):
            self.parse_module(node)
        elif isinstance(node, ast.Assign):
            self.parse_assign(node)
        elif isinstance(node, ast.FunctionDef):
            self.parse_func_def(node)
        elif isinstance(node, ast.ClassDef):
            self.parse_class_def(node)
        elif isinstance(node, (ast.Return, ast.Num, ast.Pass, ast.Str)):
            pass
        else:
            raise NotImplementedError("No logic yet implemented for node {}".format(node))

    def parse_code(self, code):
        self.parse(ast.parse(code))

    def variables(self):
        return self.__variables

    def lookup_variables(self, var, ignore_parent=False):
        """
        Lookup a type for a variable.
        """
        variables = self.__variables
        if var in variables:
            return variables[var]

        if self.__parent_env is not None and not ignore_parent:
            return self.__parent_env.lookup_types(var)

        return None


