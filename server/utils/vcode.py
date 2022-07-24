import random
from typing import Any


class VerificationCode(object):
    def digits(self, ndigits: int = 6, code_cast_func: Any = str) -> Any:
        """
        Digits verification code, default 6 digits string.
        ``ndigits`` indicates the length of the code to return.
        ``code_cast_func`` a callable used to cast the code return value.
        """
        return code_cast_func(
            random.randrange(10 ** (ndigits - 1), 10 ** ndigits)
        )


_global_instance = VerificationCode()
digits = _global_instance.digits
