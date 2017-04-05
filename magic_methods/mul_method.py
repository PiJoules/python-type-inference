from function_type import BuiltinFunction


class MulMethod(BuiltinFunction):
    def __init__(self):
        super().__init__(
            self.MUL_METHOD,
            pos_args=["self", "other"]
        )
