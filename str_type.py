import class_type


class StrClass(class_type.ClassType):
    def __init__(self):
        super().__init__("str")



def create_class():
    from function_type import BuiltinFunction

    # Create the class
    cls = StrClass()

    # Add any methods
    class StripMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                pos_args=["self"],
                keywords=["chars"],
                keyword_defaults=[{cls.instance()}],
            )
        def call(self, args):
            return {cls.instance()}

    class FormatMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                pos_args=["self"],
                vararg="args",
                kwarg="kwargs",
            )
        def call(self, args):
            return {cls.instance()}

    class GetItemMethod(BuiltinFunction):
        def __init__(self):
            super().__init__(
                pos_args=["self", "key"]
            )
        def call(self, args):
            return {cls.instance()}

    cls.set_attr("strip", {StripMethod()})
    cls.set_attr("format", {FormatMethod()})
    cls.set_attr("__getitem__", {GetItemMethod()})

    return cls


STR_CLASS = create_class()
