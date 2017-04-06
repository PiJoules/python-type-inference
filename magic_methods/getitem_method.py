from function_type import BuiltinFunction


class GetItemMethod(BuiltinFunction):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            defined_name=self.GETITEM_METHOD,
            pos_args=["self", "key"],
            **kwargs
        )
