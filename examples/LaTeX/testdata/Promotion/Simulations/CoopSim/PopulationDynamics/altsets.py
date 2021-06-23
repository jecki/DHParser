# altsets.py - This is a slightly adjusted version of the altsets module 
# that was submitted to the Active State Programmer Network by Raymond
# Hettinger. It has been included in the Plotter package to allow for 
# compatibility with Jython (Python 2.1). The sets module that comes along
# with Python 2.3 is only backwards compatible to version 2.2

# Original Source see: http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/230113
#
# Title: Implementation of sets using sorted lists
# Submitter: Raymond Hettinger (other recipes)
# Last Updated: 2003/10/21
# Version no: 1.0
# Category: Algorithms
# 	
# Description:
# 
# Inspired by Py2.3s TimSort, this implementation of sets.py uses sorted lists 
# instead of dictionaries. For clumped data patterns, the set operations can be 
# super-efficient (for example, two sets can be determined to be disjoint with 
# only O(n) comparisons). Also note, that the set elements are *not* required 
# to be hashable; this provides a great deal more freedom than dictionary based 
# implementations.


""" altsets.py -- An alternate implementation of Sets.py

Implements set operations using sorted lists as the underlying data structure.

Advantages:

  * Space savings -- lists are much more compact than a dictionary
    based implementation.

  * Flexibility -- elements do not need to be hashable, only __cmp__
    is required.

  * Fast operations depending on the underlying data patterns.
    Non-overlapping sets get united, intersected, or differenced
    with only log(N) element comparisons.  Results are built using
    fast-slicing.

  * Algorithms are designed to minimize the number of compares
    which can be expensive.

  * Natural support for sets of sets.  No special accomodation needs to
    be made to use a set or dict as a set member, but users need to be
    careful to not mutate a member of a set since that may breaks its
    sort invariant.

Disadvantages:

  * Set construction uses list.sort() with potentially N log(N)
    comparisons.

  * Membership testing and element addition use log(N) comparisons.
    Element addition uses list.insert() with takes O(N) time.

ToDo:

   * Make the search routine adapt to the data; falling backing to
     a linear search when encountering random data.

"""

from bisect import bisect_left, insort_left

class Set:

    def __init__(self, iterable):
        data = list(iterable)
        data.sort()
        result = data[:1]
        for elem in data[1:]:
            if elem == result[-1]:
                continue
            result.append(elem)
        self.data = result
        
    def __repr__(self):
        return 'Set(' + repr(self.data) + ')'

    def __iter__(self):
        return iter(self.data)

    def __contains__(self, elem):
        data = self.data
        i = bisect_left(self.data, elem, 0)
        return i<len(data) and data[i] == elem

    def add(self, elem):
        insort_left(self.data, elem)

    def remove(self, elem):
        data = self.data
        i = bisect_left(self.data, elem, 0)
        if i<len(data) and data[i] == elem:
            del data[i]
 
    def _getotherdata(other):
        if not isinstance(other, Set):
            other = Set(other)
        return other.data
    #_getotherdata = staticmethod(_getotherdata)

    def __cmp__(self, other, cmp=cmp):
        return cmp(self.data, Set._getotherdata(other))

    def union(self, other, find=bisect_left):
        i = j = 0
        x = self.data
        y = Set._getotherdata(other)
        result = Set([])        
        append = result.data.append
        extend = result.data.extend
        try:
            while 1:
                if x[i] == y[j]:
                    append(x[i])
                    i += 1
                    j += 1
                elif x[i] > y[j]:
                    cut = find(y, x[i], j)
                    extend(y[j:cut])
                    j = cut
                else:
                    cut = find(x, y[j], i)
                    extend(x[i:cut])
                    i = cut
        except IndexError:
            extend(x[i:])
            extend(y[j:])
        return result

    def intersection(self, other, find=bisect_left):
        i = j = 0
        x = self.data
        y = Set._getotherdata(other)
        result = Set([])        
        append = result.data.append
        try:
            while 1:
                if x[i] == y[j]:
                    append(x[i])
                    i += 1
                    j += 1
                elif x[i] > y[j]:
                    j = find(y, x[i], j)
                else:
                    i = find(x, y[j], i)
        except IndexError:
            pass
        return result
    
    def difference(self, other, find=bisect_left):
        i = j = 0
        x = self.data
        y = Set._getotherdata(other)
        result = Set([])        
        extend = result.data.extend
        try:
            while 1:
                if x[i] == y[j]:
                    i += 1
                    j += 1
                elif x[i] > y[j]:
                    j = find(y, x[i], j)
                else:
                    cut = find(x, y[j], i)
                    extend(x[i:cut])
                    i = cut
        except IndexError:
            extend(x[i:])
        return result

    def symmetric_difference(self, other, find=bisect_left):
        i = j = 0
        x = self.data
        y = Set._getotherdata(other)
        result = Set([])
        extend = result.data.extend
        try:
            while 1:
                if x[i] == y[j]:
                    i += 1
                    j += 1
                elif x[i] > y[j]:
                    cut = find(y, x[i], j)
                    extend(y[j:cut])
                    j = cut
                else:
                    cut = find(x, y[j], i)
                    extend(x[i:cut])
                    i = cut
        except IndexError:
            extend(x[i:])
            extend(y[j:])
        return result







