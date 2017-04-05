from class_type import ClassType
from function_type import BuiltinFunction
from magic_methods import *
from generator_type import GENERATOR_CLASS

from bool_type import BOOL_TYPE


class StrStripMethod(BuiltinFunction):
    def __init__(self, chars_def):
        super().__init__(
            "strip",
            pos_args=["self"],
            keywords=["chars"],
            keyword_defaults=[chars_def],
        )

    def returns(self):
        return self.env().lookup("self")


class StrFormatMethod(BuiltinFunction):
    def __init__(self):
        super().__init__(
            "format",
            pos_args=["self"],
            vararg="args",
            kwarg="kwargs",
        )

    def returns(self):
        return self.env().lookup("self")


class StrLowerMethod(BuiltinFunction):
    def __init__(self):
        super().__init__(
            "lower",
            pos_args=["self"],
        )

    def returns(self):
        return self.env().lookup("self")


class StrGetItemMethod(GetItemMethod):
    def returns(self):
        return self.env().lookup("self")


class StrIterMethod(IterMethod):
    def returns(self):
        return {GENERATOR_CLASS.instance(yields=self.env().lookup("self"))}


class StrContainsMethod(ContainsMethod):
    def returns(self):
        return {BOOL_TYPE}


class StrClass(ClassType):
    def __init__(self):
        super().__init__(
            "str",
            init_methods=(
                StrFormatMethod(),
                StrGetItemMethod(),
                StrLowerMethod(),
                StrIterMethod(),
                StrContainsMethod(),
            )
        )

        self.set_builtin_method(StrStripMethod({self}))


STR_CLASS = StrClass()
STR_TYPE = STR_CLASS.instance()
