from function_type import BuiltinFunction


class AddMethod(BuiltinFunction):
    def __init__(self):
        super().__init__(
            defined_name=self.ADD_METHOD,
            pos_args=["self", "other"],
        )
