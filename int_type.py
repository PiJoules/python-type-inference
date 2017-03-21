import class_type


class IntClass(class_type.ClassType):
    def __init__(self):
        super().__init__("int")


def create_class():
    # Create the class
    cls = IntClass()

    # Add any methods
    pass

    return cls


INT_CLASS = create_class()
