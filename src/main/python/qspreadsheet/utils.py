#!/usr/bin/env python3
from functools import reduce


def column_ord(str):
    return reduce(lambda x, y: x * 26 + (ord(y) - 64), str, 0)


def column_chr(num):
    name = ''
    while num:
        num, rem = divmod(num - 1, 26)
        name = chr(65 + rem) + name
    return name
