from pytype import PyType


class MetaclassType(PyType):
    def __init__(self, builtins, cls_type, **kwargs):
        """
        Args:
            cls_type: The class type this meta type returns
        """
        from class_type import ClassType
        super().__init__("type", builtins, parents=[self], **kwargs)
        self.__cls_type = cls_type
        assert isinstance(self.__cls_type, ClassType)

    def inst(self, *args, **kwargs):
        return self.__cls_type

    def call(self, args):
        cls_inst = self.inst()
        cls_inst.call_new(args)
        return {cls_inst}

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return hash(self) == hash(other)




class ClassType(PyType):
    def __init__(self, builtins, inst_type, **kwargs):
        super().__init__("type", builtins, **kwargs)


import unittest


class TestMetaClassType(unittest.TestCase):
    def setUp(self):
        pass

    def test_creation(self):
        """Test we can create a metaclass."""


if __name__ == "__main__":
    unittest.main()
