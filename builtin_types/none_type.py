from class_type import ClassType


class NoneClass(ClassType):
    def __init__(self):
        super().__init__("None")


NONE_CLASS = NoneClass()
NONE_TYPE = NONE_CLASS.instance()
