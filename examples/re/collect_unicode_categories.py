#!/usr/bin/env python3

"""collect_unicode_categories.py - collects all characters with a certain Unicode category"""


import unicodedata


def pick(selector) -> list[tuple[int, str]]:   # e.g. selector = "isdecimal"
    all_digits: list[tuple[int, str]] = []
    for codepoint in range(0x110000):  # Unicode range ends at 0x10FFFF
        char = chr(codepoint)
        check = getattr(char, selector)
        if check():
            all_digits.append((codepoint, unicodedata.name(char, '')))
    return all_digits


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



if __name__ == "__main__":
    for selector in ("isdecimal", "isspace", "isalpha", "isalnum", "isidentifier"):
        print('\n' + selector + ":")
        all_elements = pick(selector)
        print(len(all_elements), all_elements[:100])
        intervals = as_intervals([e[0] for e in all_elements])
        print(len(intervals), intervals[:100])


