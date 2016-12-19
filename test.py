import random

def test():
    if random.random() < 0.5:
        return 1 # type: float
    return "a"

print(test())
