from function_type import FunctionType


class MulMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            self.MUL_METHOD, builtins,
            pos_args=["self", "other"]
        )
