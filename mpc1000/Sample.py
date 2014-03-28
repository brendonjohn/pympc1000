#!/usr/bin/env python
from .utils import class_factory, int_in_range_validator


def sample_name_validator(value):
    valid_name_characters = (
        "abcdefghijklmnopqrstuvwxyz"
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        "1234567890"
        "!#$%&'()-@_{} \x00"
    )
    value = str(value)
    if len(value) > 16:
        raise ValueError('string too long')
    for c in value:
        if c not in valid_name_characters:
            raise ValueError('invalid character: {0!r}'.format(c))
    return value


Sample = class_factory(
    class_name='Sample',
    doc='MPC 1000 Sample',
    format=(
        '<'  # Little-endian
        '16s'  # Sample Name
        'x'  # Padding
        'B'  # Level
        'B'  # Range Upper
        'B'  # Range Lower
        'h'  # Tuning
        'B'  # Play Mode       0="One Shot", 1="Note On"
        'x'  # Padding
    ),
    format_attrs=(
        ('sample_name', sample_name_validator),
        ('level', int_in_range_validator(0, 100)),
        ('range_upper', int_in_range_validator(0, 127)),
        ('range_lower', int_in_range_validator(0, 127)),
        ('tuning', int_in_range_validator(-3600, 3600)),
        ('play_mode', int_in_range_validator(0, 1)),
    ),
)