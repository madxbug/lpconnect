from decimal import Decimal, InvalidOperation
from typing import Union


def prettify_number(num: Union[float, str, Decimal, None]) -> str:
    if num is None:
        return 'N/A'

    try:
        n = num if isinstance(num, Decimal) else Decimal(str(num))
    except InvalidOperation:
        return 'N/A'

    if n.is_nan():
        return 'N/A'
    if n.is_zero():
        return '0'

    abs_n = abs(n)

    # Unicode subscript digits
    subscripts = ['₀', '₁', '₂', '₃', '₄', '₅', '₆', '₇', '₈', '₉']

    def format_small_number(number: Decimal) -> str:
        if number.is_zero():
            return '0'
        e = number.as_tuple().exponent
        m = ''.join(map(str, number.as_tuple().digits[:5]))  # Up to 5 significant digits
        zero_count = max(-e - 1, 0)  # Ensure zero_count is not negative
        subscript_zeros = ''.join(subscripts[int(digit)] for digit in str(zero_count))
        sign = '-' if number < 0 else ''
        return f"{sign}0.0{subscript_zeros}{m}"

    # Very small numbers
    if abs_n < Decimal('0.000001'):
        return format_small_number(n)

    # Numbers between 0.000001 and 0.001
    if abs_n < Decimal('0.001'):
        return f"{n:.6f}"

    # Numbers between 0.001 and 1
    if abs_n < 1:
        return f"{n:.4f}"

    # Numbers between 1 and 100
    if abs_n < 100:
        return f"{n:.2f}"

    # Numbers between 100 and 1,000
    if abs_n < 1000:
        return f"{n:.1f}"

    # Numbers between 1,000 and 1,000,000
    if abs_n < 1000000:
        return f"{n:,.0f}"

    # Numbers between 1,000,000 and 1,000,000,000 (Millions)
    if abs_n < 1000000000:
        return f"{n / 1000000:,.1f}M"

    # Numbers 1,000,000,000 and above (Billions)
    return f"{n / 1000000000:,.1f}B"
