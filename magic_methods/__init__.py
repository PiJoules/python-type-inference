from .lt_method import LtMethod

from .add_method import AddMethod
from .sub_method import SubMethod
from .mul_method import MulMethod
from .truediv_method import TrueDivMethod

from .iadd_method import IAddMethod

from .iter_method import IterMethod
from .contains_method import ContainsMethod

from .getitem_method import GetItemMethod


from function_type import FunctionType
class NextMethod(FunctionType):
    def __init__(self, builtins):
        super().__init__(
            self.NEXT_METHOD, builtins,
            pos_args=["self"]
        )
