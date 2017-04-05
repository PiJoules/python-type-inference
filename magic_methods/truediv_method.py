from function_type import BuiltinFunction


class TrueDivMethod(BuiltinFunction):
    def __init__(self):
        super().__init__(
            self.TRUEDIV_METHOD,
            pos_args=["self", "other"]
        )
