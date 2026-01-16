"""runranges.py - Set algebraic operations and fast lookup for ranges of Unicode-characters."""

from typing import NamedTuple, Sequence, List, Tuple

__all__ = ('RuneRange',
           'contains',
           'RR',
           'RRstr',
           'is_sorted_and_merged',
           'never_empty',
           'sort_and_merge',
           'range_union',
           'range_difference',
           'range_intersection')


# Character ranges algebra...

class RuneRange(NamedTuple):
    low: int
    high: int


def contains(ranges: Sequence[RuneRange], r: int) -> bool:
    highest = len(ranges) - 1
    a = 0
    b = highest
    last_i = -1
    i = b >> 1

    while i != last_i:
        rng = ranges[i]
        if rng.low <= r:
            if r <= rng.high:
                return True
            else:
                a = min(i + 1, highest)
        else:
            b = max(i - 1, 0)
        last_i = i
        i = a + (b - a) >> 1
    return False


def RR(low: str, high: str) -> RuneRange:
    return RuneRange(ord(low), ord(high))


def RRstr(s: str) -> RuneRange:
    assert len(s) == 3 and s[1] == '-'
    return RR(s[0], s[2])


def is_sorted_and_merged(rr: Sequence[RuneRange]) -> bool:
    for i in range(1, len(rr)):
        if rr[i].low <= rr[i - 1].high: return False
    return True


def never_empty(rr: Sequence[RuneRange]) -> bool:
    if len(rr) <= 0: return False
    for r in rr:
        if r.low > r.high: return False
    return True


def sort_and_merge(R: List[RuneRange]):
    Rlen = len(R)
    R.sort(key=lambda r: r.low)
    a = 0
    b = 1
    while b < Rlen:
        if R[b].low <= R[a].high + 1:
            if R[a].high <= R[b].high:
                # high(R[a]) := high(R[b])
                R[a] = RuneRange(R[a].low, R[b].high)
        else:
            a += 1
            if a != b: R[a] = R[b]
        b += 1
    del R[a + 1:]
    assert is_sorted_and_merged(R)


def range_union(A: Sequence[RuneRange], B: Sequence[RuneRange]) -> List[RuneRange]:
    R = [r for r in A]
    R.extend(B)
    sort_and_merge(R)
    return R


def range_difference(A: Sequence[RuneRange], B: Sequence[RuneRange]) \
        -> List[RuneRange]:
    assert never_empty(A) and never_empty(B)
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
        if S.low <= M.high and M.low <= S.high:
            if M.low < S.low:
                result.append(RuneRange(M.low, S.low - 1))
                if S.high < M.high:
                    M = RuneRange(S.high + 1, M.high)  # need to create a new object, here!
                    nextB()
                elif nextA():
                    return result
            elif S.high < M.high:# need to create a new object, here!
                M = RuneRange(S.high + 1, M.high)
                nextB()
            elif nextA():
                return result
        elif M.high < S.low:
            result.append(M)
            if nextA():
                return result
        else:
            assert S.high < M.low
            nextB()
    result.append(M)
    while i < lenA:
        result.append(A[i])
        i += 1
    assert is_sorted_and_merged(result)
    return result


def range_intersection(A: Sequence[RuneRange], B: Sequence[RuneRange]) \
        -> List[RuneRange]:
    C = range_difference(A, B)
    return range_difference(A, C)


def union_with_compl(A: Tuple[bool, Sequence[RuneRange]], B: Tuple[bool, Sequence[RuneRange]]) \
        -> Tuple[bool, List[RuneRange]]:
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


def diff_with_compl(A: Tuple[bool, Sequence[RuneRange]], B: Tuple[bool, Sequence[RuneRange]]) \
        -> Tuple[bool, List[RuneRange]]:
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


def intersect_with_compl(A: Tuple[bool, Sequence[RuneRange]], B: Tuple[bool, Sequence[RuneRange]]) \
        -> Tuple[bool, List[RuneRange]]:
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