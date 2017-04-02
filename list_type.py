from instance_type import InstanceType
from class_type import ClassType


class IterableType(InstanceType):
    def __hash__(self):
        raise NotImplementedError

    def __eq__(self):
        raise NotImplementedError

    def __bool__(self):
        raise NotImplementedError

    def __str__(self):
        raise NotImplementedError


LIST_NAME = "list"


class ListType(IterableType):
    def __init__(self, init_contents=None, *args, **kwargs):
        super().__init__(LIST_NAME, *args, **kwargs)

        # Combine all contents into one set. Order will not matter for
        # indexing lists.
        contents = set()
        for types in init_contents or []:
            contents |= types
        self.__contents = contents

    def contents(self):
        """
        Returns:
            set[pytype.PyType]: Set of all types in the contents
        """
        return self.__contents

    def __hash__(self):
        # Let the hash of a list type be determined by the contents
        return hash(frozenset(self.contents()))

    def __eq__(self, other):
        if not isinstance(other, ListType):
            return False

        return self.contents() == other.contents()

    def __bool__(self):
        return bool(self.contents())

    def __str__(self):
        str_contents = list(map(str, self.contents()))
        return "{}{}".format(self.name(), str_contents)


class ListClass(ClassType):
    def instance(self, *args, **kwargs):
        return ListType(parents=[self], *args, **kwargs)


def create_class():
    from getitem_method import GetItemMethod
    from int_type import INT_CLASS
    from slice_type import SLICE_CLASS

    cls = ListClass()

    class ListGetItemMethod(GetItemMethod):
        def adjusted_call(self, args):
            self.check_pos_args(args)

            results = set()
            self_types, key_types = args.pos_args()

            for self_t in self_types:
                for key_t in key_types:
                    if key_t == INT_CLASS.instance():
                        # Accessing 1 item in the tuple
                        results |= self_t.contents()
                    elif key_t == SLICE_CLASS.instance():
                        results.add(cls.instance(init_contents=[self_t.contents()]))
                    else:
                        raise RuntimeError("Unable to index {} with key {}".format(self_t, key_t))

            return results

    cls.set_attr(cls.GETITEM_METHOD, {ListGetItemMethod()})

    return cls


LIST_CLASS = create_class()
