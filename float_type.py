import class_type


class FloatClass(class_type.ClassType):
    def __init__(self):
        super().__init__("float")


def create_class():
    from function_type import BuiltinFunction

    # Create the class
    cls = FloatClass()

    # Add any methods
    class AddMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                pos_args=["self", "other"]
            )

        def call(self, args):
            return {cls.instance()}

    class SubMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                pos_args=["self", "other"]
            )

        def call(self, args):
            return {cls.instance()}

    class MulMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                pos_args=["self", "other"]
            )

        def call(self, args):
            return {cls.instance()}

    class TrueDivMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                pos_args=["self", "other"]
            )

        def call(self, args):
            return {cls.instance()}

    cls.set_attr(cls.ADD_METHOD, {AddMethod()})
    cls.set_attr(cls.SUB_METHOD, {SubMethod()})
    cls.set_attr(cls.MUL_METHOD, {MulMethod()})
    cls.set_attr(cls.TRUEDIV_METHOD, {TrueDivMethod()})

    return cls


FLOAT_CLASS = create_class()
