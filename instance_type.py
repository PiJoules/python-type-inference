import pytype
import function_type
import bound_method


class InstanceType(pytype.PyType):
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
        if attr not in self.__attrs:
            return self.__class.get_attr(attr)
        else:
            return self.__attrs[attr]
