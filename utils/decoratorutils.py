__copyright__ = "Copyright (c) 2018-2019 Alex Laird"
__license__ = "MIT"


def conditional_decorator(dec, condition):
    def decorator(func):
        if not condition:
            return func
        return dec(func)

    return decorator
