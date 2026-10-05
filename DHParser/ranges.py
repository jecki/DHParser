# ranges.py - Set algebraic operations for number-ranges.
#
# Copyright 2026  by Eckhart Arnold (arnold@badw.de)
#                 Bavarian Academy of Sciences an Humanities (badw.de)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.  See the License for the specific language governing
# permissions and limitations under the License.

"""Module ``ranges`` provides set algebraic operations for number-ranges.
This is useful for handling subsets of a text but also for fast lookup
of characters in subsets (say, all greek letters) of Unicode-characters."""


from typing import NamedTuple, Sequence, List, Tuple, TypeAlias

__all__ = ('Range',
           'contains',
           'RR',
           'RRstr',
           'is_sorted_and_merged',
           'never_empty',
           'sort_and_merge',
           'range_union',
           'range_difference',
           'range_intersection',
           'union_with_compl',
           'diff_with_compl',
           'intersect_with_compl')

# Character ranges algebra...

# class Range(NamedTuple):
#     low: int
#     high: int

Range: TypeAlias = Tuple[int, int]


def contains(ranges: Sequence[Range], r: int) -> bool:
    highest = len(ranges) - 1
    a = 0
    b = highest
    last_i = -1
    i = b >> 1

    while i != last_i:
        rng = ranges[i]
        if rng[0] <= r:
            if r <= rng[1]:
                return True
            else:
                a = min(i + 1, highest)
        else:
            b = max(i - 1, 0)
        last_i = i
        i = a + (b - a) >> 1
    return False


def RR(low: str, high: str) -> Range:
    return (ord(low), ord(high))


def RRstr(s: str) -> Range:
    assert len(s) == 3 and s[1] == '-'
    return RR(s[0], s[2])


def is_sorted_and_merged(rr: Sequence[Range]) -> bool:
    for i in range(1, len(rr)):
        if rr[i][0] <= rr[i - 1][1]: return False
    return True


def never_empty(rr: Sequence[Range]) -> bool:
    if len(rr) <= 0: return False
    for r in rr:
        if r[0] > r[1]: return False
    return True


def never_invalid(rr: Sequence[Range]) -> bool:
    if len(rr) <= 0: return False
    for r in rr:
        if r[0] - r[1] > 1: return False
    return True


def sort_and_merge(R: List[Range]):
    Rlen = len(R)
    R.sort(key=lambda r: r[0])
    a = 0
    b = 1
    while b < Rlen:
        if R[b][0] <= R[a][1] + 1:
            if R[a][1] <= R[b][1]:
                # high(R[a]) := high(R[b])
                R[a] = (R[a][0], R[b][1])
        else:
            a += 1
            if a != b: R[a] = R[b]
        b += 1
    del R[a + 1:]
    assert is_sorted_and_merged(R)


def range_union(A: Sequence[Range], B: Sequence[Range]) -> List[Range]:
    R = [r for r in A]
    R.extend(B)
    sort_and_merge(R)
    return R


def range_difference(A: Sequence[Range], B: Sequence[Range]) \
        -> List[Range]:
    if not A:  return []
    if not B:  return list(A)
    assert never_empty(A) # and never_empty(B)
    assert is_sorted_and_merged(A) and is_sorted_and_merged(B)

    result = []
    lenB = len(B)
    lenA = len(A)
    i = 1
    k = 0
    M = A[0]
    S = B[0]

    def nextA() -> bool:
        nonlocal i, A, M, lenA
        if i < lenA:
            M = A[i]
            i += 1
            return False
        return True

    def nextB():
        nonlocal k, B, S, lenB
        k += 1
        if k < lenB:
            S = B[k]

    while k < lenB:
        if S[0] <= M[1] and M[0] <= S[1]:
            if M[0] < S[0]:
                result.append((M[0], S[0] - 1))
                if S[1] < M[1]:
                    M = (S[1] + 1, M[1])  # need to create a new object, here!
                    nextB()
                elif nextA():
                    return result
            elif S[1] < M[1]:# need to create a new object, here!
                M = (S[1] + 1, M[1])
                nextB()
            elif nextA():
                return result
        elif M[1] < S[0]:
            result.append(M)
            if nextA():
                return result
        else:
            assert S[1] < M[0]
            nextB()
    result.append(M)
    while i < lenA:
        result.append(A[i])
        i += 1
    assert is_sorted_and_merged(result)
    return result


def range_intersection(A: Sequence[Range], B: Sequence[Range]) \
        -> List[Range]:
    C = range_difference(A, B)
    return range_difference(A, C)


def union_with_compl(A: Tuple[bool, Sequence[Range]], B: Tuple[bool, Sequence[Range]]) \
        -> Tuple[bool, List[Range]]:
    if A[0]:
        if B[0]:
            return True, range_intersection(B[1], A[1])
        else:
            return True, range_difference(A[1], B[1])
    else:
        if B[0]:
            return True, range_intersection(B[1], A[1])
        else:
            return False, range_union(A[1], B[1])


def diff_with_compl(A: Tuple[bool, Sequence[Range]], B: Tuple[bool, Sequence[Range]]) \
        -> Tuple[bool, List[Range]]:
    if A[0]:
        if B[0]:
            return False, range_difference(B[1], A[1])
        else:
            return True, range_union(A[1], B[1])
    else:
        if B[0]:
            return False, range_intersection(A[1], B[1])
        else:
            return False, range_difference(A[1], B[1])


def intersect_with_compl(A: Tuple[bool, Sequence[Range]], B: Tuple[bool, Sequence[Range]]) \
        -> Tuple[bool, List[Range]]:
    if A[0]:
        if B[0]:
            return True, range_union(B[1], A[1])
        else:
            return False, range_difference(B[1], A[1])
    else:
        if B[0]:
            return False, range_difference(A[1], B[1])
        else:
            return False, range_intersection(A[1], B[1])