"""add_club_finance must locate the finance block even when a club name is invalid UTF-8.

Synthetic buffer, no save needed. Run: python3 tests/test_club_he.py
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fm_editor.gamedb import find_clubs, add_club_finance, _NULL_DATES


def build(name: bytes, short: bytes, balance: int):
    r = bytearray(struct.pack('<I', 3))               # at+0 club id
    r += struct.pack('<I', 7) * 2                     # at+4 uid, at+8 uid
    r += b'\x00' + struct.pack('<I', 5)               # at+12 zero, at+13 nation
    r += b'\xff\xff\xff\xff' + b'\x00' * 4            # at+17 ff*4, pad
    r += struct.pack('<I', 5)                         # at+25 nation
    r += b'\x00' * (39 - len(r))
    r += struct.pack('<I', len(name)) + name + struct.pack('<I', len(short)) + short
    r += b'\x01'                                      # status at he
    r += b'\x00' * 8                                  # he+1..he+8 (b[he+8]=0 board entries)
    r += b'\x00'                                      # le = he+9: "small" variant
    r += struct.pack('<i', balance) + b'\x00' * 4     # le+1 balance, le+5..le+8
    r += _NULL_DATES
    r += b'\x00' * 40
    return bytes(b'\x00' * 20 + r)


def test_invalid_utf8_name():
    for name in (b'Good FC', b'Bad\xff\xfeFC'):
        b = build(name, b'BAD', 123456)
        clubs = find_clubs(b, len(b))
        assert len(clubs) == 1, clubs
        add_club_finance(b, clubs, len(b))
        assert clubs[0].get('fin') == {'balance': 123456}, (name, clubs[0])


if __name__ == '__main__':
    test_invalid_utf8_name()
    print('OK')
