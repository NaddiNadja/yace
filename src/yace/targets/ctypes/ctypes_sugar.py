"""
Addition to ctypes, making it slightly nicer to use, including:

* typedef additions
  * c_log_double_t
  * c_uint128
  * c_int128
  * void

TODO

* Dict-accessor for structs / unions
* Convenient typecast-helpers

Copyright (c) 2023 Simon A. F. Lund <os@safl.dk>
SPDX-License-Identifier: BSD-3-Clause
"""

import ctypes
from typing import TypeAlias

c_int128 = ctypes.c_ubyte * 16
c_uint128 = c_int128
void: TypeAlias = None


class Enum(object):
    """Encapsulation of C enum"""

    def from_param(self):
        return ctypes.c_int

    pass


class Structure(ctypes.Structure):
    """Encapsulation of C structs"""

    pass


class Union(ctypes.Union):
    """Encapsulation of C union"""

    pass


def char_p_to_str(char_pointer, encoding="utf-8", errors="strict"):
    """Cast a C char pointer to a Python string."""

    value = ctypes.cast(char_pointer, ctypes.c_char_p).value

    if value is not None and encoding is not None:
        value = value.decode(encoding, errors=errors)

    return value


def str_to_char_p(string, encoding="utf-8"):
    """Cast a Python string to a C char pointer."""

    if encoding is not None:
        try:
            string = string.encode(encoding)
        except AttributeError:
            # In Python3, bytes has no encode attribute
            pass

    string = ctypes.c_char_p(string)

    return ctypes.cast(string, ctypes.POINTER(ctypes.c_char))
