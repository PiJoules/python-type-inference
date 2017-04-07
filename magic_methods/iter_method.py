from function_type import FunctionType


class IterMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            self.ITER_METHOD, builtins,
            pos_args=["self"],
        )
