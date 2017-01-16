#!/usr/bin/env python
# -*- coding: utf-8 -*-

import ast
import json


if __debug__:
    ENV_COUNTER = 1


CALL_STACK = set()  # ids of instances that get called


"""
Helper functions
"""

def first(iterable):
    return next(iter(iterable))


"""
Types available at runtime
"""

class PyType:
    def __init__(self, name, ref_node=None, ref_env=None, pos_args=None,
                 keyword_args=None, varargs=None, kwargs=None,
                 method_owner=None, init_attrs=None):
        """
        Create the new function type this instance represents since all
        function definitions are unique instances.

        Args:
            name (str)
            ref_node (ast.FunctionDef)
            ref_env (Environment): The environment this instance was created in

            pos_args (Optional[tuple[str]])
            keyword_args (Optional[dict[str, set[Instance]]])
            varargs (Optional[str])
            kwargs (Optional[str])
            method_owner (Optional[Instance])
            init_attrs (Optional[dict[str, set[Instance]]])
        """
        # Add to the types
        self.__name = name
        self.__attrs = init_attrs or {}

        self.__ref_node = ref_node
        self.__ref_env = ref_env
        self.__method_owner = method_owner

        # Save the arguments
        self.__pos_args = pos_args or tuple()
        self.__keyword_args = keyword_args or {}
        self.__varargs = varargs
        self.__kwargs = kwargs

        # Add the arguments as new variables with no types for now
        args = {}
        if pos_args:
            if method_owner is None:
                for arg in pos_args:
                    args[arg] = set()
            else:
                args[pos_args[0]] = {method_owner}
                for arg in pos_args[1:]:
                    args[arg] = set()
        if kwargs:
            for arg, vals in kwargs.items():
                args[arg] = vals
        if varargs:
            args[varargs] = {AnyInst()}  # should be tuple instance containing any type
        if kwargs:
            args[kwargs] = {AnyInst()}  # should be dict instance containing any type

        # The environment of this body
        # Create it but do not parse it
        if ref_env:
            self.__body_env = Environment(
                types=ref_env.types(),
                variables=args,
                parent=self.__ref_env,
                owner=name,
            )
        else:
            self.__body_env = None

    def name(self):
        return self.__name

    def env(self):
        return self.__body_env

    def add_attr(self, attr, val):
        """
        Add an attribute to this type of object.

        Args:
            attr (str)
            val (PyType)
        """
        self.__add_attrs(attr, {val})

    def add_attrs(self, attr, vals):
        """
        Add mutliple values for a given attribute to the type.

        Args:
            attr (str)
            val (set[PyType]))
        """
        assert isinstance(vals, set)
        assert all(isinstance(x, Instance) for x in vals)

        if __debug__:
            print("adding {} for type {}: {}".format(attr, self.name(), vals))

        if attr not in self.__attrs:
            self.__attrs[attr] = vals
        else:
            self.__attrs[attr] |= vals

    def get_attr(self, attr, default=None):
        val = self.__attrs.get(attr, default)
        if __debug__:
            print("getting {} for type {}: {}".format(attr, self.name(), val))
        return val

    def attrs(self):
        return self.__attrs

    def json(self):
        attrs = {attr: val.type().name() for attr, val in self.attrs().items()}

        args = {
            "positional": self.__pos_args,
            "keyword": {arg: [inst.type().name() for inst in insts]
                        for arg, insts in self.__keyword_args.items()},
            "varargs": self.__varargs,
            "kwargs": self.__kwargs,
        }

        return_types = [inst.type().name() for inst in self.returns()]

        return {
            "attrs": attrs,
            "args": args,
            "returns": return_types,
        }

    def apply_call_node_args(self, node, env):
        """
        Parse the arguments of a call node then apply_call_args.

        Args:
            args (node.Call)
        """
        self.apply_call_args(
            pos_args=tuple(env.eval_inst(a) for a in node.args),
            keyword_args={kw.arg: env.eval_inst(kw.value)
                          for kw in node.keywords},
            # TODO: Handle varargs and kwargs later
        )

    def apply_call_args(self, pos_args=None, keyword_args=None, varargs=None,
                        kwargs=None):
        """
        Update the environment of this body

        Args:
            pos_args (Optional[tuple[set[Instance]]])
            keyword_args (Optional[dict[str, set[Instance]]])
            varargs (Optional[Tuple])
            kwargs (Optional[Dictionary])
        """
        pos_args = pos_args or tuple()
        if self.__method_owner is None:
            start = 0
        else:
            # Ignore the first arg
            start = 1
        for i, arg in enumerate(self.__pos_args[start:]):
            self.__body_env.bind(arg, pos_args[i])

        keyword_args = keyword_args or {}
        for i, (arg, defaults) in enumerate(self.__keyword_args):
            self.__body_env.bind(arg, keyword_args[arg])

        # TODO: Handle varargs and kwargs later

    def returns(self):
        """
        Run through the code to find any return statements.
        """
        if self.__ref_node is None:
            return set()
        returns = set()

        stack = list(self.__ref_node.body)
        while stack:
            node = stack.pop()
            if isinstance(node, ast.Return):
                returns |= self.__body_env.eval_inst(node.value)
            elif isinstance(node, (ast.If, ast.While, ast.For)):
                stack += node.body + node.orelse
            elif isinstance(node, ast.Try):
                stack += node.body + node.orelse + node.finalbody
                for handler in node.handlers:
                    stack += handler.body
            elif isinstance(node, ast.With):
                stack += node.body
            else:
                # Parse everything else
                self.__body_env.parse(node)

        if __debug__:
            print("returns for", self.__body_env.env_lineage(), ":", returns)

        return returns or {NoneInst()}


class ClassType(PyType):
    def __init__(self, name, ref_node, ref_env):
        """
        Create the class type and the instance type of this class.
        """
        super().__init__(name, ref_node=ref_node, ref_env=ref_env)

        # Create and add the instance type
        self.__inst = InstanceInst(name, ref_node, ref_env)

        # Run the body and add attributes to the class
        env = Environment(
            types=ref_env.types(),
            parent=ref_env,
            owner=name,
        )
        env.parse_sequence(ref_node.body)
        for var, insts in env.variables().items():
            self.add_attrs(var, insts)

    def apply_call_args(self, pos_args=None, keyword_args=None, varargs=None,
                        kwargs=None):
        """
        Update the environment of the body of the __init__ method if provided.

        Args:
            pos_args (Optional[tuple[set[Instance]]])
            keyword_args (Optional[dict[str, set[Instance]]])
            varargs (Optional[Tuple])
            kwargs (Optional[Dictionary])
        """
        init_funcs = self.__inst.type().get_attr("__init__")
        if init_funcs is None:
            return
        for func in init_funcs:
            func.type().apply_call_args(
                pos_args=pos_args,
                keyword_args=keyword_args,
                varargs=varargs,
                kwargs=kwargs,
            )

    def returns(self):
        """
        Create and return an instance of this class.

        Be sure to call the __init__ method also.
        """
        init_funcs = self.__inst.type().get_attr("__init__", default=set())
        for func in init_funcs:
            func.type().returns()
        return {self.__inst}



class MockType(PyType):
    pass


"""
Instances created at runtime or are builtin instances available at startup
"""

class Instance:
    def __init__(self, inst_type):
        self.__type = inst_type

    def type(self):
        return self.__type

    def __ne__(self, other):
        return not (self == other)

    def __eq__(self, other):
        """For comparing instances at runtime."""
        raise NotImplementedError

    def __hash__(self):
        """For separating between different types in a set of instances."""
        raise NotImplementedError


class BaseInstance(Instance):
    """Instances of types where the runtime properties do not matter."""
    def __eq__(self, other):
        return isinstance(other, type(self))

    def __hash__(self):
        """Hash is just a hash of the name of this type of instance."""
        return hash(self.type().name())


class IntInst(BaseInstance):
    def __init__(self):
        super().__init__(INT_TYPE)

class FloatInst(BaseInstance):
    def __init__(self):
        super().__init__(FLOAT_TYPE)

class ComplexInst(BaseInstance):
    def __init__(self):
        super().__init__(COMPLEX_TYPE)

class NoneInst(BaseInstance):
    def __init__(self):
        super().__init__(NONE_TYPE)

class AnyInst(BaseInstance):
    def __init__(self):
        super().__init__(ANY_TYPE)

class BoolInst(BaseInstance):
    def __init__(self):
        super().__init__(BOOL_TYPE)


class FunctionInst(Instance):
    def __eq__(self, other):
        return self.type().name() == other.type().name()

    def __hash__(self):
        """All function instances are unique."""
        return hash(self.type().name())


class BuiltinFunctionInst(FunctionInst):
    def __init__(self, name):
        # Add to the types
        func_type = PyType(name)
        TYPES[name] = func_type
        super().__init__(func_type)


class PrintFunction(BuiltinFunctionInst):
    def __init__(self):
        super().__init__("print")


class DefinedFunctionInst(Instance):
    def __init__(self, name, ref_node, ref_env, pos_args=None,
                 keyword_args=None, varargs=None, kwargs=None,
                 method_owner=None):
        """
        Create the new function type this instance represents since all
        function definitions are unique instances.

        Args:
            name (str)
            ref_node (ast.FunctionDef)
            ref_env (Environment): The environment this instance was created in

            pos_args (Optional[tuple[str]])
            keyword_args (Optional[dict[str, set[Instance]]])
            varargs (Optional[str])
            kwargs (Optional[str])
            method_owner (Optional[Instance])
        """
        # Add to the types
        func_type = PyType(name, ref_node=ref_node, ref_env=ref_env,
                           pos_args=pos_args, keyword_args=keyword_args,
                           varargs=varargs, kwargs=kwargs,
                           method_owner=method_owner)
        ref_env.types()[name] = func_type
        super().__init__(func_type)

    @classmethod
    def from_node(cls, node, env, method_owner=None):
        name = node.name
        args = node.args
        body = node.body

        # Extract args
        # Pos args
        pos_args = tuple(a.arg for a in args.args[:len(args.args)-len(args.defaults)])

        # Keywrod args
        keyword_args = {}
        for i, arg in enumerate(args.args[len(args.args)-len(args.defaults):]):
            keyword_args[arg.arg] = env.eval_inst(args.defaults[i])
        for i, kwarg in enumerate(args.kwonlyargs):
            default = args.kw_defaults[i]
            if default is None:
                keyword_args[kwarg.arg] = set()
            else:
                keyword_args[kwarg.arg] = env.eval_inst(default)

        # Varibale args
        if args.vararg:
            varargs = args.vararg.arg
        else:
            varargs = None

        # kwargs
        if args.kwarg:
            kwargs = args.kwarg.arg
        else:
            kwargs = None

        return cls(name, node, env, pos_args=pos_args, keyword_args=keyword_args,
                   varargs=varargs, kwargs=kwargs, method_owner=method_owner)

    def __eq__(self, other):
        return self.type().name() == other.type().name()

    def __hash__(self):
        """All function instances are unique."""
        return hash(self.type().name())


class InstanceInst(Instance):
    def __init__(self, name, ref_node, ref_env):
        # Create and add the instance type
        inst_name = name + "_instance"
        inst_type = PyType(inst_name)
        ref_env.types()[inst_name] = inst_type
        super().__init__(inst_type)

        # Run the body and add attributes to the inst
        env = Environment(
            types=ref_env.types(),
            parent=ref_env,
            owner=inst_name,
            method_owner=self,
        )
        env.parse_sequence(ref_node.body)
        for var, insts in env.variables().items():
            self.type().add_attrs(var, insts)

    def __eq__(self, other):
        return self.type().name() == other.type().name()

    def __hash__(self):
        return hash(self.type().name())


class ClassInst(Instance):
    def __init__(self, name, ref_node, ref_env):
        """
        Create the class type and the instance type of this class.
        """
        # Add class to the types
        cls_type = ClassType(name, ref_node, ref_env)
        ref_env.types()[name] = cls_type
        super().__init__(cls_type)

    @classmethod
    def from_node(cls, node, env):
        return cls(node.name, node, env)
    def __eq__(self, other):
        return id(self) == id(other)

    def __hash__(self):
        """All function instances are unique."""
        return id(self)


"""
Instance mocks for testing
"""

class MockInstance(Instance):
    def __init__(self, name):
        super().__init__(MockType(name + "_instance"))

    def __eq__(self, other):
        return self.type().name() == other.type().name()

    def __hash__(self):
        return hash(self.type().name())


class MockFunction(Instance):
    def __init__(self, name):
        super().__init__(MockType(name))

    def __eq__(self, other):
        return self.type().name() == other.type().name()

    def __hash__(self):
        return hash(self.type().name())


class Environment:
    def __init__(self, types=None, variables=None, parent=None, owner=None,
                 method_owner=None):
        #self.__owner = owner or "<module>" # for debugging
        self.__owner = owner

        self.__types = dict(types or {})
        self.__variables = dict(variables or {})
        self.__parent = parent
        self.__uncalled_funcs = set()
        self.__uncalled_classes = set()
        self.__method_owner = method_owner

    def bind(self, var, insts):
        assert isinstance(insts, set)
        assert all(isinstance(x, Instance) for x in insts)

        if not var in self.__variables:
            self.__variables[var] = insts
        else:
            self.__variables[var] |= insts

    """
    Debugging methods
    """

    def env_lineage(self):
        """
        Returns:
            str
        """
        if self.__parent is None:
            return self.__owner
        else:
            return self.__parent.env_lineage() + "->" + self.__owner


    """
    Type inference
    """

    def eval_num(self, node):
        n = node.n
        if isinstance(n, int):
            return {IntInst()}
        elif isinstance(n, float):
            return {FloatInst()}
        elif isinstance(n, complex):
            return {ComplexInst()}
        else:
            raise RuntimeError("Unknown num type {}".format(n))

    def eval_call(self, node):
        """
        Apply the arguments to the function body environmnen then evaluate the
        return type.
        """
        funcs = self.eval_inst(node.func)

        if __debug__:
            print("calling:", funcs, "in env", self.env_lineage())

        returns = set()
        for func in funcs:
            # Ignore previously called functions
            if func in CALL_STACK:
                continue

            CALL_STACK.add(func)

            func.type().apply_call_node_args(node, self)
            returns |= func.type().returns()

            CALL_STACK.remove(func)
        return returns

    def eval_name(self, node):
        """
        Return a copy of the set of instances.
        """
        vals = self.lookup(node.id)
        if vals is None:
            raise RuntimeError("Variable '{}' not previously declared in env {}.".format(node.id, self.env_lineage()))
        return set(vals)

    def eval_binop(self, node):
        """
        The interpreter actually calls the __whatever__ method of the first
        object in the binary operation, but for now, just return the set of
        both types of the expressions.
        """
        returns = set()
        returns |= self.eval_inst(node.left)
        returns |= self.eval_inst(node.right)
        return returns

    def eval_attr(self, node):
        val = node.value
        attr = node.attr  # str

        insts = self.eval_inst(val)
        returns = set()
        for inst in insts:
            inst_type = inst.type()
            returns |= inst_type.get_attr(attr, default=set())
        return returns

    def eval_compare(self, node):
        """
        Comparisons always return boolean values.
        """
        return {BoolInst()}

    def eval_inst(self, node):
        if __debug__:
            print("evaluating instance:", node)

        if isinstance(node, ast.Num):
            return self.eval_num(node)
        elif isinstance(node, ast.Call):
            return self.eval_call(node)
        elif isinstance(node, ast.Name):
            return self.eval_name(node)
        elif isinstance(node, ast.BinOp):
            return self.eval_binop(node)
        elif isinstance(node, ast.Attribute):
            return self.eval_attr(node)
        elif isinstance(node, ast.Compare):
            return self.eval_compare(node)
        else:
            raise NotImplementedError("Unable to infer type for node {}".format(node))


    """
    Parsing ast
    """

    def parse_assign(self, node):
        """
        TODO: Unpack variables during assignment.
        """
        targets = node.targets
        value = node.value  # ast node
        insts = self.eval_inst(value)

        for target in targets:
            if isinstance(target, ast.Name):
                self.bind(target.id, insts)
            elif isinstance(target, ast.Attribute):
                base = target.value  # ast node
                attr = target.attr  # str
                base_insts = self.eval_inst(base)
                for inst in base_insts:
                    # Set the attribute for each instance
                    inst.type().add_attrs(attr, insts)
            else:
                raise NotImplementedError("Unable to assign to target node {}".format(target))

    def parse_func_def(self, node):
        """
        Create a new function instance and add this one to a set of uncalled
        functions.
        """
        name = node.name
        func_inst = DefinedFunctionInst.from_node(node, self, method_owner=self.__method_owner)  # This creates the instance and the type
        #self.__types[name] = func_inst
        self.__uncalled_funcs.add(func_inst)

        # Add to env also
        self.bind(name, {func_inst})

    def parse_class_def(self, node):
        """
        Similar to parse_func_def, but the body is evaluated and all variable
        declarations are added as attributes of the class and its instance.
        """
        name = node.name
        class_inst = ClassInst.from_node(node, self)  # This creates the instance and the type
        self.__uncalled_classes.add(class_inst)

        if __debug__:
            print("class {} has attrs {}".format(name, class_inst.type().attrs()))

        # Add to env also
        self.bind(name, {class_inst})

    def parse_if(self, node):
        """
        Check the conditions then the bodies.
        """
        self.eval_inst(node.test)
        self.parse_sequence(node.body)
        self.parse_sequence(node.orelse)

    def parse(self, node):
        if __debug__:
            print("parsing:", node, "in env", self.env_lineage())

        if isinstance(node, ast.Module):
            self.parse_module(node)
        elif isinstance(node, ast.Assign):
            self.parse_assign(node)
        elif isinstance(node, ast.FunctionDef):
            self.parse_func_def(node)
        elif isinstance(node, ast.ClassDef):
            self.parse_class_def(node)
        elif isinstance(node, ast.Expr):
            self.eval_inst(node.value)
        elif isinstance(node, ast.If):
            self.parse_if(node)
        #elif isinstance(node, (ast.If, ast.While, ast.For)):
        #    stack += node.body + node.orelse
        #elif isinstance(node, ast.Try):
        #    stack += node.body + node.orelse + node.finalbody
        #    for handler in node.handlers:
        #        stack += handler.body
        #elif isinstance(node, ast.With):
        #    stack += node.body
        elif isinstance(node, ast.Pass):
            pass
        else:
            raise NotImplementedError("Cannot parse node {}".format(node))

    def parse_sequence(self, seq):
        for node in seq:
            self.parse(node)

    def parse_module(self, node):
        self.parse_sequence(node.body)

        # Last minute check
        assert not CALL_STACK, "Call stack not empty in env: {}".format(CALL_STACK)

    def parse_code(self, code):
        self.parse(ast.parse(code))


    """
    Getters
    """

    def lookup(self, var, ignore_parent=False):
        if var in self.__variables:
            return self.__variables[var]

        if not ignore_parent and self.__parent:
            return self.__parent.lookup(var)

        return None

    def types(self):
        """
        Returns:
            dict[str, PyType]
        """
        return self.__types

    def variables(self):
        """
        Returns:
            dict[str, set[Instance]]
        """
        return self.__variables

    def available_variables(self):
        """
        All variables that can be accessed by in this env, including those
        in parent envs.
        """
        variables = {}
        variables.update(self.variables())
        if self.__parent:
            variables.update(self.__parent.available_variables())
        return variables

    def json(self):
        variables = {}
        for var, insts in self.variables().items():
            variables[var] = [inst.type().name() for inst in insts]
        types = {}
        for name, t in self.types().items():
            types[name] = t.json()
        return {
            "variables": variables,
            "types": types,
        }


class ModuleEnv(Environment):
    def __init__(self, types=None, variables=None, parent=None, owner=None,
                 method_owner=None):
        super().__init__(types=TYPES, variables=BUILTIN_INSTS,
                         owner="<module>")


INT_TYPE = PyType("int")
FLOAT_TYPE = PyType("float")
COMPLEX_TYPE = PyType("complex")
NONE_TYPE = PyType("None")
ANY_TYPE = PyType("Any")
BOOL_TYPE = PyType("bool")


# All types known to all environments
# Populated with builtin types initially and filled at runtime with user-defined
# types
TYPES = {
    "int": INT_TYPE,
    "float": FLOAT_TYPE,
    "complex": COMPLEX_TYPE,
    "None": NONE_TYPE,
    "bool": BOOL_TYPE,
}


BUILTIN_INSTS = {
    "print": {PrintFunction()}
}


def get_args():
    from argparse import ArgumentParser
    parser = ArgumentParser("Python type inference")

    parser.add_argument("filename", help="Filename to type check.")

    args = parser.parse_args()
    return args


def main():
    args = get_args()

    with open(args.filename) as f:
        env = ModuleEnv()
        env.parse_code(f.read())
        print(json.dumps(env.json(), indent=4))

    return 0


if __name__ == "__main__":
    main()


