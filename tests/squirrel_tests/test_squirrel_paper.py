"""test_squirrel_paper.py  - The examples from Luke Hutchinson's Squirrel-Parser paper,
p. 21, https://github.com/lukehutch/squirrelparser/blob/main/paper/squirrel_parser.pdf

Uncomment the return-statement at the beginning of the show() function to see the parse trees!
"""


import sys, os

from DHParser.nodetree import flatten_sxpr
from DHParser.dsl import create_parser


scriptpath = os.path.dirname(__file__) or '.'
sys.path.append(os.path.abspath(os.path.join(scriptpath, '..')))
scriptpath = os.path.abspath(scriptpath)


def show(result):
    # return  # uncomment to see parse trees!
    print()
    print(result.as_tree(fancy=True))
    # print(flatten_sxpr(result.as_sxpr()))


class TestSquirrelLeftRecursion:
    def test_direct_left_recursion(self):
        parser = create_parser("A = (A 'x') | 'x'\n")
        assert parser is not None
        result = parser("xxx")
        assert result.as_sxpr() == '(A (A (A "x") (:Text "x")) (:Text "x"))'
        show(result)

    def test_indirect_left_recursion(self):
        parser = create_parser("A = B | 'x'\n"
                               "B = (A 'y') | (A 'x')\n")
        assert parser is not None
        result = parser("xxyx")
        assert result.as_sxpr() == \
               '(A (B (A (B (A (B (A "x") (:Text "x"))) (:Text "y"))) (:Text "x")))'
        show(result)

    def test_input_dependent_left_recursion_1(self):
        parser = create_parser("A = B | 'z'\n"
                               "B = ('x' A) | (A 'y')\n")
        assert parser is not None
        result = parser("xxzyyy")
        assert flatten_sxpr(result.as_sxpr()) == \
            '(A (B (:Text "x") (A (B (:Text "x") (A (B (A (B (A (B (A "z") ' \
            '(:Text "y"))) (:Text "y"))) (:Text "y")))))))'
        show(result)

    def test_input_dependent_left_recursion_2(self):
        parser = create_parser("A = 'x'? (A 'y' | A | 'y')")
        assert parser is not None
        result = parser("xxyyy")
        assert flatten_sxpr(result.as_sxpr()) == \
            '(A (:Text "x") (A (:Text "x") (A (A (A "y") (:Text "y")) (:Text "y"))))'
        show(result)

    def test_interwoven_left_recursion_3_cycles(self):
        parser = create_parser("""
            S = E
            E = F 'n' | 'n'
            F = E '+' I* | G '-'
            G = H 'm' | E
            H = G 'l'
            I = '(' A+ ')'
            A = 'a'""")
        assert parser is not None
        result = parser('nlm-n+(aaa)n')
        assert flatten_sxpr(result.as_sxpr()) == \
                         '(S (E (F (E (F (G (H (G (E "n")) (:Text "l")) ' \
                         '(:Text "m")) (:Text "-")) (:Text "n")) (:Text "+") ' \
                         '(I (:Text "(") (A "a") (A "a") (A "a") (:Text ")"))) (:Text "n")))'
        show(result)

    def test_interwoven_left_recursion_2_cycles(self):
        parser = create_parser("""
            M = L
            L = P ".x" | 'x'
            P = P "(n)" | L""")
        assert parser is not None
        result = parser('x.x(n)(n).x.x')
        assert flatten_sxpr(result.as_sxpr()) == \
            '(M (L (P (L (P (P (P (L (P (L "x")) (:Text ".x"))) ' \
            '(:Text "(n)")) (:Text "(n)")) (:Text ".x"))) (:Text ".x")))'
        show(result)

    def test_explicit_left_associativity(self):
        parser = create_parser("""
            E = E '+' N | N
            N = /[0-9]+/""")
        assert parser is not None
        result = parser('0+1+2+3')
        assert flatten_sxpr(result.as_sxpr()) == \
            '(E (E (E (E (N "0")) (:Text "+") (N "1")) (:Text "+") (N "2")) (:Text "+") (N "3"))'
        show(result)

    def test_explicit_right_associativity(self):
        parser = create_parser("""
            E = N '+' E | N
            N = /[0-9]+/""")
        assert parser is not None
        result = parser('0+1+2+3')
        assert flatten_sxpr(result.as_sxpr()) == \
            '(E (N "0") (:Text "+") (E (N "1") (:Text "+") ' \
            '(E (N "2") (:Text "+") (E (N "3")))))'
        show(result)

    def test_ambiguous_associativity(self):
        parser = create_parser("""
            E = E '+' E | N
            N = /[0-9]+/""")
        assert parser is not None
        result = parser('0+1+2+3')
        assert flatten_sxpr(result.as_sxpr()) == \
            '(E (E (N "0")) (:Text "+") (E (E (N "1")) (:Text "+") ' \
            '(E (E (N "2")) (:Text "+") (E (N "3")))))'
        show(result)

if __name__ == "__main__":
    from DHParser.testing import runner
    runner("", globals())