__author__ = "Alex Laird"
__copyright__ = "Copyright 2019, Alex Laird"
__version__ = "0.1.5"


def conditional_decorator(dec, condition):
    def decorator(func):
        if not condition:
            return func
        return dec(func)

    return decorator
