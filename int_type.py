import class_type


class IntClass(class_type.ClassType):
    def __init__(self):
        super().__init__("int")


def create_class():
    from function_type import BuiltinFunction

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

    cls.set_attr(cls.ADD_METHOD, {AddMethod()})

    return cls


INT_CLASS = create_class()
