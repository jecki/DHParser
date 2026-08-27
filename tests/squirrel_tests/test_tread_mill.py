# ===========================================================================
# SECTION 9: LEFT RECURSION (10 tests)
# ===========================================================================

from test_utils import run_test_parse


LR1 = '''
    S <- "'" N "'" ;
    N <- ( "(" N ")" )* ;
'''

def test_tread_mill_1():
    result = run_test_parse(LR1, "''")
    assert result.ok, "should succeed"
    assert result.error_count == 0, "should have 0 errors"

def test_tread_mill_2():
    result = run_test_parse(LR1, "'()'")
    assert result.ok, "should succeed"
    assert result.error_count == 0, "should have 0 errors"
