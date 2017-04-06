import pytype
import class_type
import instance_type

from magic_methods import *


class TupleType(instance_type.InstanceType):
    def __init__(self, *args, init_contents=None, **kwargs):
        """
        Args:
            init_contents (Optional[tuple[set[pytype.PyType]]])
        """
        super().__init__("tuple", *args, **kwargs)

        self.__contents = init_contents or tuple()

        assert isinstance(self.__contents, tuple)
        for types in self.__contents:
            assert isinstance(types, set)
            assert all(isinstance(x, pytype.PyType) for x in types)

    def contents(self):
        return self.__contents

    def all_contents(self):
        """
        Returns:
            set[pytype.PyType]: Set of all types in the contents
        """
        ret_types = set()
        for types in self.contents():
            ret_types |= types
        return ret_types

    def __hash__(self):
        # Tuple hash depends on hashs of contents
        return hash(self.name())

    def __eq__(self, other):
        # Tuples are equal if the contents are equal
        if not isinstance(other, TupleType):
            return False

        own_contents = self.contents()
        other_contents = other.contents()

        if len(own_contents) != len(other_contents):
            return False

        for i in range(len(own_contents)):
            if own_contents[i] != other_contents[i]:
                return False

        return True

    def __bool__(self):
        return bool(self.contents())

    def __str__(self):
        str_contents = list(set(map(str, types)) for types in self.contents())
        return "tuple{}".format(str_contents)


class TupleClass(class_type.ClassType):
    def create_tuple(self, **kwargs):
        return TupleType(parents=[self], **kwargs)

    def call(self, args):
        if args:
            if len(args.pos_args()) != 1:
                raise RuntimeError("Tuple only accepts up to 1 argument.")
            types = args.pos_args()[0]
            return {self.create_tuple(init_contents=t.contents()) for t in types}
        else:
            return {self.create_tuple()}

    def instance(self, *args, **kwargs):
        return self.create_tuple(*args, **kwargs)


def create_tuple_class():
    from function_type import BuiltinFunction

    cls = TupleClass("tuple")

    class TupleGetItemMethod(GetItemMethod):
        def adjusted_call(self, args):
            self.check_pos_args(args)

            results = set()
            self_types, key_types = args.pos_args()

            for self_t in self_types:
                for key_t in key_types:
                    if key_t.is_type(self.builtins().int()):
                        # Accessing 1 item in the tuple
                        results |= self_t.all_contents()
                    else:
                        raise RuntimeError("Unable to index {} with key {}".format(self_t, key_t))

            return results

    class TupleIterMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                defined_name=self.ITER_METHOD,
                pos_args=["self"]
            )

        def adjusted_call(self, args):
            self.check_pos_args(args)
            results = set()
            self_types = args.pos_args()[0]

            for self_t in self_types:
                results |= self_t.all_contents()

            return {self.builtins().generator().instance(yields=results)}

    cls.set_attr(cls.GETITEM_METHOD, {TupleGetItemMethod()})
    cls.set_attr(cls.ITER_METHOD, {TupleIterMethod()})

    return cls
