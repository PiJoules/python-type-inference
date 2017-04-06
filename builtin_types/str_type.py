from class_type import ClassType
from function_type import BuiltinFunction
from magic_methods import *

from builtin_types import *


class StrStripMethod(BuiltinFunction):
    def __init__(self):
        super().__init__(
            "strip",
            pos_args=["self"],
            keywords=["chars"],
            keyword_defaults=[self.builtins().str()],
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
        return {self.generator().instance(yields=self.env().lookup("self"))}


class StrContainsMethod(ContainsMethod):
    def returns(self):
        return {self.builtins().bool()}


class StrIAddMethod(IAddMethod):
    def returns(self):
        return self.env().lookup("self")


class StrClass(ClassType):
    def __init__(self):
        super().__init__(
            "str",
            init_methods=(
                StrStripMethod(),
                StrFormatMethod(),
                StrGetItemMethod(),
                StrLowerMethod(),
                StrIterMethod(),
                StrContainsMethod(),
                StrIAddMethod(),
            )
        )
