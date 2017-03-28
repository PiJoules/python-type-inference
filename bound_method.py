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

    def update_args(self, args):
        """
        Add the owner as the first positional arg then pass to regular
        update_args.
        """
        args.prepend_owner(self.owner())
        super().update_args(args)

    def owner(self):
        """
        Returns:
            instance_type.InstanceType
        """
        return self.__owner
