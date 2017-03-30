import class_type


class IntClass(class_type.ClassType):
    def __init__(self):
        super().__init__("int")


def create_class():
    from function_type import BuiltinFunction
    from float_type import FLOAT_CLASS

    # Create the class
    cls = IntClass()

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
            return {FLOAT_CLASS.instance()}

    class TrueDivMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                pos_args=["self", "other"]
            )

        def call(self, args):
            return {FLOAT_CLASS.instance()}

    cls.set_attr(cls.ADD_METHOD, {AddMethod()})
    cls.set_attr(cls.SUB_METHOD, {SubMethod()})
    cls.set_attr(cls.MUL_METHOD, {MulMethod()})
    cls.set_attr(cls.TRUEDIV_METHOD, {TrueDivMethod()})

    return cls


INT_CLASS = create_class()
