from function_type import BuiltinFunction


class IterMethod(BuiltinFunction):
    def __init__(self):
        super().__init__(
            defined_name=self.ITER_METHOD,
            pos_args=["self"],
        )
