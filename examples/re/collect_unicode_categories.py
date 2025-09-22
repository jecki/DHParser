#!/usr/bin/env python3

"""collect_unicode_categories.py - collects all characters with a certain Unicode category"""


import unicodedata


def as_intervals(elements: list[int]) -> list[tuple[int, int]]:
    """Converts a list of integers into a list of intervals."""
    elements.sort()
    intervals: list[tuple[int, int]] = []
    start = elements[0]
    last = start
    for element in elements[1:]:
        if element == last + 1:
            last = element
            continue
        intervals.append((start, last))
        start = element
        last = element
    intervals.append((start, last))
    return intervals


def digits() -> list[tuple[int, str]]:
    all_digits: list[tuple[int, str]] = []
    for codepoint in range(0x110000):  # Unicode range ends at 0x10FFFF
        char = chr(codepoint)
        if char.isdecimal():
            all_digits.append((codepoint, unicodedata.name(char, '')))
    return all_digits


def whitespaces() -> list[tuple[int, str]]:
    all_whitespaces: list[tuple[int, str]] = []
    for codepoint in range(0x110000):  # Unicode range ends at 0x10FFFF
        char = chr(codepoint)
        if char.isspace():
            all_whitespaces.append((codepoint, unicodedata.name(char, '')))
    return all_whitespaces


def alphanums() -> list[tuple[int, str]]:
    all_alphanum: list[tuple[int, str]] = []
    for codepoint in range(0x110000):  # Unicode range ends at 0x10FFFF
        char = chr(codepoint)
        if char.isalnum():
            all_alphanum.append((codepoint, unicodedata.name(char, '')))
    return all_alphanum


if __name__ == "__main__":
    all_digits = digits()
    print(len(all_digits), all_digits)
    intervals = as_intervals([d[0] for d in all_digits])
    print(len(intervals), intervals)

    all_whitespaces = whitespaces()
    print(len(all_whitespaces), all_whitespaces)
    intervals = as_intervals([w[0] for w in all_whitespaces])
    print(len(intervals), intervals)

    all_alphanums = alphanums()
    print(len(all_alphanums)) # , all_alphanums)
    intervals = as_intervals([an[0] for an in all_alphanums])
    print(len(intervals), intervals)

