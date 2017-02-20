import pytype
import function_type


class BoundMethod(function_type.FunctionType):
    @classmethod
    def from_function_type(cls, func_type, inst):
        """
        The first argument is automatically bounded to the instance this
        belongs to.
        """
        raise NotImplementedError
