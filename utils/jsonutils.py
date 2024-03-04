__copyright__ = "Copyright (c) 2018-2019 Alex Laird"
__license__ = "MIT"

import decimal


def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError
