# Compatibility

"""Provides code snipplets for ompatibility with older python versions.
"""

#-------------------------------------------------------------------------------
#
# sets module
#
#-------------------------------------------------------------------------------

try:
    set
except NameError:
    try:
        import sets
    except ImportError:
        import altsets as sets
    set = sets.Set    

#-------------------------------------------------------------------------------
#
# boolean values "True" and "False"
#
#-------------------------------------------------------------------------------

try:
    True, False
except NameError:
    True, False = (0==0, 0!=0)


#-------------------------------------------------------------------------------
#
# new style classes derived from "object"
#
#-------------------------------------------------------------------------------
    
try:
    object
except NameError:
    class object:
        pass


#-------------------------------------------------------------------------------
#
# define jython flag
#
#-------------------------------------------------------------------------------

try:
    import java
    jython = True
except:
    jython = False
    

#-------------------------------------------------------------------------------
#
# sum function
#
#-------------------------------------------------------------------------------

try:
    sum
except NameError:
    sum = lambda l: reduce(lambda a,b:a+b, l)

        
#-------------------------------------------------------------------------------
#
# numerical arrays 
#
#-------------------------------------------------------------------------------


try:
    from Numeric import array, ravel, matrixmultiply, dot, concatenate, \
                        diagonal, putmask, identity, asarray, zeros, \
                        logical_and, logical_or
    UInt8 = "u"
    from RandomArray import uniform
    def all(a):
        return logical_and.reduce(ravel(a))
    def any(a):
        return logical_or.reduce(ravel(a))
    HAS_NUMERIC = True
except:
    try:
        from numarray import array, ravel, matrixmultiply, dot, concatenate, \
                             diagonal, putmask, identity, asarray, zeros, \
                             all, any, UInt8
        from numarray.random_array import uniform
        HAS_NUMERIC = True        
    except:
        from ArrayWrapper import array, ravel, matrixmultiply, concatenate, \
                                 diagonal, asarray, zeros, all, any
        UInt8 = ""
        HAS_NUMERIC = False

# for testing:
##from ArrayWrapper import *
##HAS_NUMERIC = False


