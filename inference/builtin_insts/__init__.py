# -*- coding: utf-8 -*-

import inference


class IntClassInstance(inference.ClassInstance):
    def call(self, args=None):
        """
        Args to this class provided in
        https://docs.python.org/3/library/functions.html#int
        """
        return IntInstance()


class IntInstance(inference.Instance):
    def __init__(self, **kwargs):
        super().__init__("int", **kwargs)


class MockInt(IntInstance):
    def __eq__(self, other):
        """
        Just check if the types match up.
        """
        return isinstance(other, IntInstance)


print(type(MockInt()))
print(isinstance(MockInt(), IntInstance))
print(MockInt().__hash__)
print(IntInstance().__hash__)


INT_CLASS = IntClassInstance()
