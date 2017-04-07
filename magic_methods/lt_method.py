from function_type import FunctionType


class LtMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            self.LT_METHOD, builtins,
            pos_args=["self", "other"],
        )
