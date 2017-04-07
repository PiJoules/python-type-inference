# -*- coding: utf-8 -*-

import ast
import sys
import os
import astor
import pytype
import function_type
import class_type

from arguments import Arguments, empty_args


class Environment:
    def __init__(self, name, builtins, init_vars=None, parent_env=None,
                 module_location=None):
        self.__name = name
        self.__builtins = builtins
        self.__variables = dict(init_vars or {})  # dict[str, set[pytype.PyType]]
        self.__parent = parent_env
        if self.__parent:
            self.__call_stack = self.__parent.call_stack()
        else:
            self.__call_stack = set()

        self.__returns = set()
        self.__yields = set()
        self.__raises = set()

        # Modules
        self.__module_location = module_location

    def builtins(self):
        return self.__builtins

    def returns(self):
        return self.__returns

    def yields(self):
        return self.__yields

    def raises(self):
        return self.__raises

    def name(self):
        return self.__name

    def call_stack(self):
        return self.__call_stack

    def variables(self):
        return self.__variables

    def all_variables(self):
        """Includes variables in higher level envs."""
        vars = {}
        if self.__parent:
            vars.update(self.__parent.all_variables())
        vars.update(self.variables())
        return vars

    def bind(self, varname, types):
        """
        Set a variable to be a set of types.

        Args:
            varname (str)
            types (set[pytype.PyType])
        """
        assert isinstance(varname, str)
        assert isinstance(types, set)
        assert all(isinstance(x, pytype.PyType) for x in types)

        if varname in self.__variables:
            self.__variables[varname] |= types
        else:
            self.__variables[varname] = set(types)  # The types are always copied

    def bind_attr(self, node, types):
        """
        Bind the attribute of a type to a set of types.

        Args:
            node (ast.Attribute)
            types (set[pytype.PyType])
        """
        value = node.value
        attr = node.attr

        value_types = self.eval(value)
        for t in value_types:
            if t.has_attr(pytype.PyType.SETATTR_METHOD):
                raise RuntimeError("TODO: Implement logic for custom defined __setattr__ methods")
            t.set_attr(attr, types)

    def exclusive_lookup(self, varname):
        """
        Lookup a variable only in this environment.
        """
        return self.__variables[varname]

    def lookup(self, varname, init_env=None):
        """
        Lookup a variable in this environment, then lookup in the parent env
        if it is not in this env.
        """
        init_env = init_env or self.name()

        if varname in self.__variables:
            return self.exclusive_lookup(varname)

        if self.__parent:
            return self.__parent.lookup(varname, init_env=init_env)

        raise KeyError("'{}' does not exist in environment of '{}'".format(varname, init_env))

    def unpack_assign(self, target, types):
        """
        Args:
            target (ast node)
            types (set[pytype.PyType])
        """
        if isinstance(target, ast.Name):
            self.bind(target.id, types)
        elif isinstance(target, ast.Attribute):
            self.bind_attr(target, types)
        elif isinstance(target, ast.Tuple):
            # Iterate through each tuple value and set the nth content to
            # the nth target
            for t in types:
                assert len(target.elts) == len(t.contents())

            src_types = [set() for i in target.elts]
            for t in types:
                for i in range(len(src_types)):
                    src_types[i] |= t.contents()[i]

            for i, elt in enumerate(target.elts):
                self.unpack_assign(elt, src_types[i])
        else:
            raise NotImplementedError("Unable to assign to target node '{}'".format(target))

    """
    Type evaluation
    """

    """
    Literals
    """

    def eval_num(self, node):
        n = node.n
        if isinstance(n, int):
            return {self.builtins().int()}
        elif isinstance(n, float):
            return {self.builtins().float()}
        else:
            raise NotImplementedError("Unknown type for num '{}'".format(type(n)))

    def eval_str(self, node):
        return {self.builtins().str()}

    def eval_bytes(self, node):
        return {self.builtins().bytes()}

    def eval_list(self, node):
        return {
            self.builtins().list_cls().from_list(list(map(self.eval, node.elts)))
        }

    def eval_tuple(self, node):
        return {
            self.builtins().tuple_cls().create_tuple(
                init_contents=tuple(self.eval(n) for n in node.elts)
            )
        }

    def eval_call(self, node):
        """
        Call, update, and evaluate the function.
        """
        ret_types = set()

        func_types = self.eval(node.func)  # set[PyType]

        for func in func_types:
            if func not in self.__call_stack:
                self.__call_stack.add(func)

                # Create new arguments since these are mutated
                args = Arguments.from_call_node(node, self)
                ret_types |= func.call(args)

                self.__call_stack.remove(func)

        return ret_types

    def eval_name(self, node):
        """
        Return a copy of the set.
        """
        return set(self.lookup(node.id))

    def eval_bin_op_from_types(self, left, op, right, aug=False):
        results = set()
        if isinstance(op, ast.Add):
            for t in left:
                results |= t.call_add(Arguments([right]), aug=aug)
        elif isinstance(op, ast.Sub):
            for t in left:
                results |= t.call_sub(Arguments([right]), aug=aug)
        elif isinstance(op, ast.Mult):
            for t in left:
                results |= t.call_mul(Arguments([right]), aug=aug)
        elif isinstance(op, ast.Div):
            for t in left:
                results |= t.call_truediv(Arguments([right]), aug=aug)
        else:
            raise NotImplementedError("No logic for handling operation {}".format(op))

        return results

    def eval_bin_op(self, node):
        """Call the appropriate magic method of each type."""
        op = node.op
        left = self.eval(node.left)
        right = self.eval(node.right)
        return self.eval_bin_op_from_types(left, op, right)

    def eval_single_compare(self, left, op, right):
        """
        Perform a comparison on a single node
        """
        results = set()
        left_types = self.eval(left)
        right_types = self.eval(right)
        if isinstance(op, ast.Eq):
            for t in left_types:
                results |= t.call_eq(Arguments([right_types]))
        elif isinstance(op, ast.Lt):
            for t in left_types:
                results |= t.call_lt(Arguments([right_types]))
        elif isinstance(op, ast.In):
            for t in left_types:
                results |= t.call_contains(Arguments([right_types]))
        else:
            raise NotImplementedError("No logic for comparing with operation {}".format(op))
        return results

    def eval_compare(self, node):
        """
        x < y > z is equivalent to (x < y) and (y > z), so the methods __lt__,
        __gt__, and __and__ and will need to be called for each appropriate
        instance.

        Returns:
            set[PyType]
        """
        left = node.left
        if len(node.ops) == 1:
            # Equivalent to just calling one of the comparison magic methods
            # No conjunctions
            return self.eval_single_compare(left, node.ops[0], node.comparators[0])

        results = set()
        comp_results = []  # Save the comparisons for testing the overall conjunction
        for i, op in enumerate(node.ops):
            right = node.comparators[i]
            comp_results.append(self.eval_single_compare(left, op, right))
            left = right

        # Perform the and-ing
        for i in range(len(comp_results)-1):
            result_types = comp_results[i]  # set[pytype.Pytype]
            for t in result_types:
                results |= t.call_and(Arguments([comp_results[i+1]]))

        return results

    def eval_attr(self, node):
        value = node.value
        attr = node.attr

        value_types = self.eval(value)

        types = set()
        for t in value_types:
            if t.has_attr(pytype.PyType.GETATTRIBUTE_METHOD):
                raise RuntimeError("TODO: Need to implement logic for handling custom __getattribute__ methods.")
            types |= t.get_attr(attr)
        return types

    def eval_subscript(self, node):
        key_types = self.eval(node.slice)
        values = self.eval(node.value)

        ret_types = set()
        for value in values:
            args = Arguments([key_types])
            ret_types |= value.call_getitem(args)
        return ret_types

    def eval_index(self, node):
        return self.eval(node.value)

    def eval_slice(self, node):
        """Create a slice type."""
        return {self.builtins().slice()}

    def eval_ext_slice(self, node):
        raise NotImplementedError

    def eval_unary_op(self, node):
        """
        Evaluate the node depending on the operation and operand

        operations:
            UAdd, USub: whatever the operand is
            Not: boolean
            Invert (~): integer
        """
        operation = node.op
        if isinstance(operation, (ast.UAdd, ast.USub)):
            return self.eval(node.operand)
        elif isinstance(operation, ast.Not):
            return {self.builtins().bool()}
        elif isinstance(operation, ast.Invert):
            return {self.builtins().int()}
        else:
            raise RuntimeError("Unknown unary operation {}".format(operation))

    def eval_name_constant(self, node):
        value = node.value
        if value is None:
            return {self.builtins().none()}
        else:
            return {self.builtins().bool()}

    def eval(self, node):
        if isinstance(node, ast.Num):
            return self.eval_num(node)
        elif isinstance(node, ast.Str):
            return self.eval_str(node)
        elif isinstance(node, ast.Bytes):
            return self.eval_bytes(node)
        elif isinstance(node, ast.List):
            return self.eval_list(node)
        elif isinstance(node, ast.Tuple):
            return self.eval_tuple(node)
        elif isinstance(node, ast.Call):
            return self.eval_call(node)
        elif isinstance(node, ast.Name):
            return self.eval_name(node)
        elif isinstance(node, ast.BinOp):
            return self.eval_bin_op(node)
        elif isinstance(node, ast.Compare):
            return self.eval_compare(node)
        elif isinstance(node, ast.Attribute):
            return self.eval_attr(node)
        elif isinstance(node, ast.Subscript):
            return self.eval_subscript(node)
        elif isinstance(node, ast.Index):
            return self.eval_index(node)
        elif isinstance(node, ast.Slice):
            return self.eval_slice(node)
        elif isinstance(node, ast.ExtSlice):
            return self.eval_ext_slice(node)
        elif isinstance(node, ast.UnaryOp):
            return self.eval_unary_op(node)
        elif isinstance(node, ast.Yield):
            if node.value:
                return self.eval(node.value)
            else:
                return {self.builtins().none()}
        elif isinstance(node, ast.Expr):
            return self.eval(node.value)
        elif isinstance(node, ast.NameConstant):
            return self.eval_name_constant(node)
        else:
            raise NotImplementedError("Unable to evaluate type for node '{}' on line {}".format(node, node.lineno))

    """
    Node parsing
    """

    def parse_arguments(self, node):
        """
        Parse function definition arguments node.

        Positional arguments have no type by default (empty set) and
        keyword arguments have the default values as their only types.

        TODO: Check for type annotations later
        """
        # Positional args
        pos_args_end = len(node.args) - len(node.kwonlyargs)
        pos_args_nodes = node.args
        for arg_node in pos_args_nodes[:pos_args_end]:
            self.bind(arg_node.arg, set())

        # Varargs
        vararg_node = node.vararg
        if vararg_node:
            # Create a new tuple which could contain different types
            self.bind(vararg_node.arg, set())

        # Keyword arguments
        for i, arg_node in enumerate(pos_args_nodes[pos_args_end:]):
            default_node = node.defaults[i]
            default_types = self.eval(default_node)
            self.bind(arg_node.arg, default_types)
        for i, kwarg_node in enumerate(node.kwonlyargs):
            default = node.kw_defaults[i]
            if default:
                types = self.eval(default)
            else:
                types = set()
            self.bind(kwarg_node.arg, types)

        # Kwargs
        kwarg_node = node.kwarg
        if kwarg_node:
            # Create a new dict which could contain different types
            self.bind(kwarg_node.arg, set())

    def parse_assign(self, node):
        targets = node.targets
        val = node.value
        types = self.eval(val)

        for target in targets:
            self.unpack_assign(target, types)

    def parse_function_def(self, node):
        """
        Add a function type to the variables.
        """
        func_type = function_type.UserDefinedFunction.from_node_and_env(node, self)
        self.bind(node.name, {func_type})

    def parse_class_def(self, node):
        cls_type = class_type.StaticClassType.from_node_and_env(node, self)
        self.bind(node.name, {cls_type})

    def parse_if(self, node):
        """
        Evaluate the test then the bodies.
        """
        self.eval(node.test)
        self.parse_sequence(node.body)
        self.parse_sequence(node.orelse)

    def parse_expr(self, node):
        results = self.eval(node.value)
        if isinstance(node.value, ast.Yield):
            self.__yields |= results

    def parse_regular_import_alias(self, node):
        """
        Parse the imported module and make all variable assignments attributes
        of a new module type.
        """
        name = node.name
        asname = node.asname or name
        mod_t = self.builtins().load_module(name)
        self.bind(asname, {mod_t})

    def parse_import(self, node):
        for alias in node.names:
            asname = alias.asname
            if asname is None:
                self.parse_regular_import_alias(alias)
            else:
                raise NotImplementedError("No logic implemented yet for handling importing aliases")

    def parse_for(self, node):
        target = node.target
        iter_node = node.iter
        body = node.body
        orelse = node.orelse

        # Bind target to whatever is yielded by the iter
        iter_types = self.eval(iter_node)
        contents = set()
        for t in iter_types:
            #contents |= t.all_contents()
            iterator_types = t.call_iter(empty_args())  # iterator
            for iter_t in iterator_types:
                # The next value
                contents |= iter_t.call_next(empty_args())
        self.unpack_assign(target, contents)

        # Parse both the body and orelse
        self.parse_sequence(body)
        self.parse_sequence(orelse)

    def parse_try(self, node):
        """
        Parse the body, handlers, orelse, and finalbody in that order.
        """
        body = node.body
        handlers = node.handlers
        orelse = node.orelse
        finalbody = node.finalbody

        self.parse_sequence(body)

        for handler in handlers:
            exc = handler.type
            asname = handler.name  # (str, None)
            exc_body = handler.body

            exc_types = self.eval(exc)
            if asname is not None:
                self.bind(asname, exc_types)

            self.parse_sequence(exc_body)

        self.parse_sequence(orelse)
        self.parse_sequence(finalbody)

    def parse_return(self, node):
        if node.value:
            self.__returns |= self.eval(node.value)

    def parse_raise(self, node):
        """
        Evaluate both the exception and cause
        """
        self.__raises |= self.eval(node.exc)
        if node.cause:
            self.eval(node.cause)

    def parse_aug_assign(self, node):
        targets = self.eval(node.target)
        values = self.eval(node.value)
        op = node.op
        results = self.eval_bin_op_from_types(targets, op, values, aug=True)
        self.unpack_assign(node.target, results)

    def parse(self, node):
        if isinstance(node, ast.Assign):
            self.parse_assign(node)
        elif isinstance(node, ast.FunctionDef):
            self.parse_function_def(node)
        elif isinstance(node, ast.arguments):
            self.parse_arguments(node)
        elif isinstance(node, ast.ClassDef):
            self.parse_class_def(node)
        elif isinstance(node, ast.If):
            self.parse_if(node)
        elif isinstance(node, ast.Expr):
            self.parse_expr(node)
        elif isinstance(node, ast.Import):
            self.parse_import(node)
        elif isinstance(node, ast.For):
            self.parse_for(node)
        elif isinstance(node, ast.Try):
            self.parse_try(node)
        elif isinstance(node, ast.Raise):
            self.parse_raise(node)
        elif isinstance(node, (ast.Pass, ast.Continue, ast.Break)):
            pass
        elif isinstance(node, ast.Return):
            self.parse_return(node)
        elif isinstance(node, ast.AugAssign):
            self.parse_aug_assign(node)
        else:
            raise NotImplementedError("Unable to parse node '{}'".format(node))

    def parse_sequence(self, seq):
        for node in seq:
            self.parse(node)

    def parse_module(self, node):
        self.parse_sequence(node.body)
        assert not self.__call_stack

    def parse_code(self, code):
        self.parse_module(ast.parse(code))
        assert not self.__call_stack


class ModuleEnv(Environment):
    def __init__(self, module_location=None):
        from builtins_manager import BuiltinsManager

        super().__init__(
            "__main__",
            BuiltinsManager(),
            init_vars=pytype.load_builtin_vars(),
            module_location=module_location)

        # Also add this location to the pythonpath
        if module_location is not None:
            sys.path.insert(1, os.path.dirname(module_location))
