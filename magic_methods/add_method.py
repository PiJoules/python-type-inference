from function_type import BuiltinFunction


class AddMethod(BuiltinFunction):
    def __init__(self):
        super().__init__(
            self.ADD_METHOD,
            pos_args=["self", "other"]
        )
