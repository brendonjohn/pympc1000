#!/usr/bin/env python
from . import DEFAULT_PGM_DATA, Program
import sys


def main():
    pgm_data_str = DEFAULT_PGM_DATA

    pgm = Program(pgm_data_str)

    if pgm:
        print 'Program loaded'
    else:
        print 'Program failed to load'
        return 1

    pgm_data = pgm.data

    if pgm_data == pgm_data_str:
        print 'Program data matches original'
    else:
        print 'Program data differs from original'
        print repr(pgm_data)
        return 2

    return 0


if __name__ == '__main__':
    status = main()
    sys.exit(status)