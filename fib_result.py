from utils import FrameTracker, GlobalFrameTracker

GLOBAL_TRACKER = GlobalFrameTracker()


@GLOBAL_TRACKER.bind_function
def fib(n):
    tracker = FrameTracker("fib")

    # Bind arguments
    tracker.bind_variable("n", n)

    tracker.call_func(bool, n < 2)
    tracker.bind_returns(n)
    tracker.bind_returns(
        tracker.call_func(fib, n-1) + tracker.call_func(fib, n-2)
    )

    return tracker.returns()


@GLOBAL_TRACKER.bind_function
def main():
    tracker = FrameTracker("main")

    tracker.call_func(
        print,
        tracker.call_func(fib, 5)
    )

    tracker.bind_returns(0)
    return tracker.returns()


GLOBAL_TRACKER.lookup("bool").call(
    GLOBAL_TRACKER.lookup("__name__").eq(
        GLOBAL_TRACKER.builtins().str_literal("__main__")
    )
)
GLOBAL_TRACKER.lookup("main").call()
