from function_type import FunctionType


class SubMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            self.SUB_METHOD, builtins,
            pos_args=["self", "other"]
        )
