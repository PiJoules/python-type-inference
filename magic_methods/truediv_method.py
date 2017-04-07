from function_type import FunctionType


class TrueDivMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            self.TRUEDIV_METHOD, builtins,
            pos_args=["self", "other"]
        )
