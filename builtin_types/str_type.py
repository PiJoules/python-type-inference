from class_type import StaticClassType
from function_type import FunctionType
from instance_type import InstanceType
from magic_methods import *


class StrStripMethod(FunctionType):
    def __init__(self, builtins, str_inst):
        super().__init__(
            "strip", builtins,
            pos_args=["self"],
            keywords=["chars"],
            keyword_defaults=[{str_inst}],
        )

    def returns(self):
        return self.env().lookup("self")


class StrFormatMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            "format", builtins,
            pos_args=["self"],
            vararg="args",
            kwarg="kwargs",
        )

    def returns(self):
        return self.env().lookup("self")


class StrLowerMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            "lower", builtins,
            pos_args=["self"],
        )

    def returns(self):
        return self.env().lookup("self")


class StrGetItemMethod(GetItemMethod):
    def returns(self):
        return self.env().lookup("self")


class StrIterMethod(IterMethod):
    def returns(self):
        return {self.builtins().generator_cls().instance(yields=self.env().lookup("self"))}


class StrContainsMethod(ContainsMethod):
    def returns(self):
        return {self.builtins().bool()}


class StrIAddMethod(IAddMethod):
    def returns(self):
        return self.env().lookup("self")


class StrClass(StaticClassType):
    def __init__(self, builtins):
        super().__init__(
            "str", builtins,
            init_methods=(
                StrFormatMethod(builtins),
                StrGetItemMethod(builtins),
                StrLowerMethod(builtins),
                StrIterMethod(builtins),
                StrContainsMethod(builtins),
                StrIAddMethod(builtins),
            )
        )
        self.set_builtin_method(StrStripMethod(builtins, self.instance()))
