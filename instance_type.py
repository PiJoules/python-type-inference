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
        from function_type import FunctionType

        super().__init__(cls_type.defined_name())
        self.__class = cls_type

        for attr, types in cls_type.attrs().items():
            # Create bound methods
            inst_attr_types = set()
            for t in types:
                if isinstance(t, FunctionType):
                    t.bind_owner(self)
                inst_attr_types.add(t)
            self.set_attr(attr, inst_attr_types)

    def get_attr(self, attr):
        """
        Check self first. If not in self, check the class.
        """
        if attr not in self.attrs():
            return self.__class.get_attr(attr)
        else:
            return super().get_attr(attr)

    def __str__(self):
        return self.name()


class InstanceMock(InstanceMixin):
    """Class for checking that a pytype is some instance when debugging."""
    def __init__(self, name):
        super().__init__(name)

