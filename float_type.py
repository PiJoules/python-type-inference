import class_type


class FloatClass(class_type.ClassType):
    def __init__(self):
        super().__init__("float")


def create_class():
    # Create the class
    cls = FloatClass()

    # Add any methods
    pass

    return cls


FLOAT_CLASS = create_class()
