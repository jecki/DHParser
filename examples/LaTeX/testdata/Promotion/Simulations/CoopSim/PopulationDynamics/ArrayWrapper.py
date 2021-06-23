import copy, random
from Compatibility import *


class array(object):
    """Wraps a function or a nested list or tuple as a multidimensional array
    Access to a cell of an ArrayWrapper object, e.g. "aw[a,b,c]" will be
    mapped to a function call "f(a,b,c)" or to a nested sequence "l[a][b][c]"
    respectively.

    The ArrayWrapper class is syntactical sugar to provide similar access to
    pay functions or lists as to Numeric or nummarray arrays.

    Warning: This wrapper does not do much error checking! Some methods
    do not work for wrapped functions!
    """

    def __str__(self):
        if self.obj != None:  return str(self.obj)
        else: return "Cannot convert wrapped function to string!"

    def __len__(self):
        assert self.obj != None, "Length of wrapped function is not defined!"
        return len(self.obj)
    
    def __init__(self, obj, *etc):
        """obj - function or tuple of list
        """
        if callable(obj):
            self.obj = None
            self.dimensions = None
            self.function = obj
        elif hasattr(obj, "__getitem__"):
            self.obj = list(obj)
            self.dimensions = []
            l = self.obj
            while type(l) == type([]):
                self.dimensions.append(len(l))
                assert l != [], "Empty lists or lists with empty lists "+\
                                "as elements cannot be wrapped!"
##                for i in xrange(len(l)):
##                    if isinstance(l[i], array):  l[i] = list(l[i])
                l = l[0]
            self.function = self.__listwrapper
        else:
            raise TypeError, "ArrayWrapper only supports callables, lists "+\
                             "or tuples, but not %s!" % type(obj)
        self.__op = None
                             
    def __listwrapper(self, *key):
        value = self.obj
        for i in key:  value = value[i]
        return value
        
    def __getitem__(self, key):
        if type(key) == type(1): return self.function(key)
        else: return self.function(*key)

    def __setitem__(self, key, value):
        if self.obj != None:
            if type(key) == type(1):
                self.obj[key] = value
            else:
                ref = self.obj
                for i in key[:-1]:  ref = ref[i]
                ref[key[-1]] = value
        else:
            raise TypeError,"wrapped functions do not support item assignement"

    def __getstate__(self):
        if self.function != self.__listwrapper:
            raise TypeError, "Can't prepare an Array Wrapper "\
                             "of a function for pickling!"
        else:
            dct = self.__dict__.copy()
            dct["function"] = None
            return dct

    def __setstate__(self, dict):
        self.__dict__.update(dict)
        self.function = self.__listwrapper        

    def __operation(self, l1, l2):
        if type(l1) == type([]):
            if type(l2) == type([]):
                return [self.__operation(x1,x2) for (x1,x2) in zip(l1,l2)]
            else:
                return [self.__operation(x,l2) for x in l1]
        else:  return self.__op(l1,l2)
    def __arithmetic(self, other, op):
        self.__op = op
        if isinstance(other, array):
            assert self.dimensions != None and other.dimensions != None,\
                "Cannot multiply wrapped functions!"
            assert self.dimensions == other.dimensions, \
                "Cannot multiply arrays with different dimensions: %s and %s"\
                % (str(self.dimensions),str(other.dimensions))
            return array(self.__operation(self.obj, other.obj))
        else:  return array(self.__operation(self.obj, other))

    def __mul__(self, other):
        """Multiply array item for item with another array of the same
        dimensions or with a scalar. This is not a matrix multiplication.
        For matrix multiplication use function 'matrixmultiply' or
        'dot' instead.
        """
        return self.__arithmetic(other, lambda x,y:x*y)

    def __add__(self, other):
        """Add array item for item with another array of the same
        dimensions or add a scalar to every element of the array.
        """
        return self.__arithmetic(other, lambda x,y:x+y)

    def __div__(self, other):
        """Divide an array elementwise by a scalar or by the elements
        of another array.
        """
        return self.__arithmetic(other, lambda x,y:x/y)
    __truediv__ = __div__

    def __eq__(self, other):
        """Elementwise test for equality."""
        if other == None: return False
        return self.__arithmetic(other, lambda x,y:x==y)
    
    def __ne__(self, other):
        """Elementwise test for equality."""
        if other == None: return True
        return self.__arithmetic(other, lambda x,y:x!=y)
    
    
    def tolist(self):
        """Returns the object as list. Not possible for wrapped functions!"""
        if self.obj != None:
            return self.obj
        else:  raise TypeError, "Cannot convert wrapped function into a list!"

    def copy(self):
        """Returns a copy of the array."""
        return copy.deepcopy(self)
    
    def diagonal(self):
        """Returns the diagonal of the array as array"""
        assert self.dimensions != None, \
               "Cannot determine the diagonal for wrapped functions!"
        ds = len(self.dimensions)
        if ds == 1:  return self.obj[0]
        return array([self.__getitem__(*((i,)*ds)) \
                      for i in xrange(len(self.obj))])
          

def asarray(seq):
    """Subsitute for Numeric.asarray."""
    return array(seq)


def dot(a, b):
    """Matrix multiplication of the arrays 'a' and 'b'"""
    assert a.dimensions != None and b.dimensions != None,\
      "Cannot multiply wrapped functions!"
    assert len(a.dimensions) <= 2 and len(b.dimensions) <= 2,\
      "Sorry, implementation does not support dot product for dimensions > 2"
    if len(a.dimensions) == 2:
        if len(b.dimensions) == 1:
            v = []
            for l in range(a.dimensions[0]):
                s = sum([a[l,c] * b[c] for c in range(a.dimensions[1])])
                v.append(s)
            return array(v)
    elif len(a.dimensions) == 1:
        if len(b.dimensions) == 1:
            return sum([a[c]*b[c] for c in range(a.dimensions[0])])
    assert False, "Sorry, matrix multiplication not yet implemented for "+\
                  "dimensions %i, %i"%(len(a.dimensions),len(b.dimensions))
matrixmultiply = dot


def flatten(l):
    """Flatten a nested list to a one dimensional list."""
    r = []
    for item in l:
        if isinstance(item, list) or isinstance(item, tuple):
            r.extend(flatten(item))
        else: r.append(item)
    return r


def ravel(array):
    """Rough replacement for Numeric.ravel!"""
    assert array.obj != None, "Cannot reshape function arrays!"
    return flatten(array.obj)


def concatenate(a, axis=0):
    """Rough replacement for Numeric.concatenate! Works only for 1-dimensional
    array. The axis parameter is ignoered!"""
    l = []
    for aw in a:  l.extend(aw.obj)
    return array(l)

def diagonal(a, *parms):
    """Rough replacement for Numeric.diagonal."""
    return a.diagonal()

def _zeros(shape):
    """Returns a list filled with zeros (floating point numbers)."""
    if len(shape) == 0:  return 0.0
    else:
        l = [_zeros(shape[:-1]) for i in xrange(shape[-1])]
        return l

def zeros(shape, typeString="d"):
    """Returns an array filled with 0.0"""
    return array(_zeros(shape))

def any(a):
    """--> true, if any of the elements of array 'a' are true."""
    for e in flatten(a.obj):
        if e: return True
    return False

def all(a):
    """--> true, if all elements of array 'a' are true."""
    for e in flatten(a.obj):
        if e: return True
    return False    

##def uniform(minimum, maximum, shape=[]):
##    """Rough replacement for RandomArray.uniform."""
##    if len(shape) == 0:  return random.uniform(minimum, maximum)
##    assert len(shape) <= 1, "Multidimensional random arrays not yet supported!"
##    return array([random.uniform(minumum, maximum) for i in range(shape[0])])
