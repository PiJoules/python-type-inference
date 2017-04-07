from function_type import FunctionType


class ContainsMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            self.CONTAINS_METHOD, builtins,
            pos_args=["self", "item"],
        )
