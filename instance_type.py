import pytype


class InstanceMixin(pytype.PyType):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __hash__(self):
        return hash(self.name())

    def __eq__(self, other):
        return isinstance(other, InstanceMixin)


class InstanceType(InstanceMixin):
    def __init__(self, cls_type):
        from bound_method import BoundMethod
        from function_type import FunctionType

        super().__init__(cls_type.defined_name())
        self.__class = cls_type

        for attr, types in cls_type.attrs().items():
            # Create bound methods
            inst_attr_types = set()
            for t in types:
                if isinstance(t, FunctionType):
                    bound_meth = BoundMethod.from_function_type(t, self)
                    inst_attr_types.add(bound_meth)
                else:
                    inst_attr_types.add(t)
            self.add_attr(attr, inst_attr_types)

    def get_attr(self, attr):
        """
        Check self first. If not in self, check the class.
        """
        if attr not in self.attrs():
            return self.__class.get_attr(attr)
        else:
            return super().get_attr(attr)


class InstanceMock(InstanceMixin):
    """Class for checking that a pytype is some instance when debugging."""
    def __init__(self, name):
        super().__init__(name)

