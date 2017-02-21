import pytype
import function_type
import bound_method


class InstanceType(pytype.PyType):
    INIT_METHOD = "__init__"

    @classmethod
    def from_class_type(cls, cls_type):
        """
        Bind all methods to the instance as bound methods.
        """
        inst = cls(cls_type.ref_node().name)

        for attr, types in cls_type.attrs().items():
            # Create bound methods
            inst_attr_types = set()
            for t in types:
                if isinstance(t, function_type.FunctionType):
                    bound_meth = bound_method.BoundMethod.from_function_type(t, inst)
                    inst_attr_types.add(bound_meth)
                else:
                    inst_attr_types.add(t)
            inst.add_attr(attr, inst_attr_types)

        return inst

    def get_attr(self, attr):
        """
        Check self first. If not in self, check the class.
        """
        if attr not in self.attrs():
            return self.__class.get_attr(attr)
        else:
            return super().get_attr(attr)

    def call_init(self, args):
        if self.INIT_METHOD in self.attrs():
            for t in self.attrs()[self.INIT_METHOD]:
                t.call_and_update(args)

    def __hash__(self):
        return hash(self.name())

    def __eq__(self, other):
        return isinstance(other, type(self))

