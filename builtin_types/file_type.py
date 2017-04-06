from class_type import ClassType


class FileClass(ClassType):
    def __init__(self):
        super().__init__("file")


FILE_CLASS = FileClass()
FILE_TYPE = FILE_CLASS.instance()
