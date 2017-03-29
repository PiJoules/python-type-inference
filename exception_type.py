import class_type


class ExceptionClass(class_type.ClassType):
    def __init__(self, name="Exception"):
        super().__init__(name)


def create_class():
    cls = ExceptionClass()

    return cls


EXCEPTION_CLASS = create_class()
