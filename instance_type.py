import pytype


class InstanceMixin(pytype.PyType):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __hash__(self):
        return hash(self.name())

    def __eq__(self, other):
        return isinstance(other, InstanceMixin)


class InstanceType(InstanceMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.parents(), "PyType '{}' does not have a ClassType to create it".format(self.name())

    def get_attr(self, attr):
        from function_type import FunctionType

        types = super().get_attr(attr)
        for t in types:
            if isinstance(t, FunctionType):
                t.bind_method(self)

        return types


class InstanceMock(InstanceMixin):
    """Class for checking that a pytype is some instance when debugging."""
    def __init__(self, name):
        super().__init__(name)

