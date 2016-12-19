#import random

def test():
    if random.random() < 0.3:
        return 1
    elif random.random() < 0.6:
        return "a"
    else:
        return {"a": 2}

print(test())
