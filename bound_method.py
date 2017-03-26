import function_type


class BoundMethod(function_type.FunctionType):
    def __init__(self, owner, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__owner = owner

    @classmethod
    def from_function_type(cls, func_type, inst):
        func = cls(inst, func_type.env(), func_type.ref_node(),
                   pos_args=func_type.pos_args(),
                   keywords=func_type.keywords(),
                   vararg=func_type.vararg(),
                   kwonlyargs=func_type.kwonlyargs(),
                   kwarg=func_type.kwarg())
        return func

    def _update_positional_args(self, args):
        """
        The first argument is automatically bounded to the instance this
        belongs to. The arguments passed to this method are unpacked among the
        remaining defined positional and keyword arguments.
        """
        defined_args = set()
        pos_args = args.pos_args()

        # First is always a reference to self
        self.env().bind(self.pos_args()[0], {self.owner()})
        defined_args.add(self.pos_args()[0])

        for i, arg in enumerate(self.pos_args()[1:]):
            self.env().bind(arg, pos_args[i])
            defined_args.add(arg)

        return defined_args

    def owner(self):
        """
        Returns:
            instance_type.InstanceType
        """
        return self.__owner
