import exception_type


class ValueErrorClass(exception_type.ExceptionClass):
    def __init__(self, name="ValueError"):
        super().__init__(name)


def create_class():
    cls = ValueErrorClass()

    return cls


VALUE_ERROR_CLASS = create_class()
