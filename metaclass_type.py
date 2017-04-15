from pytype import PyType


class MetaclassType(PyType):
    def __init__(self, builtins, cls_type, **kwargs):
        """
        Args:
            cls_type: The class type this meta type returns
        """
        super().__init__("type", builtins, parents=[self], **kwargs)
        self.__cls_type = cls_type

    def call(self, args):
        pass
