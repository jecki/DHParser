"""algorithmen.py - diverse Algorithmen für das MLW"""

import re

# fasc - itergula
# fac - iet - ergula
# fac - ist - ergula
# facite - rcu - la

testfall_facitergula = """
    facitergula
    
    fascitergula
    facietergula
    facistergula
    facitercula
    """


def teile_lemma(lemma_txt):
    return [s for s in re.split(r'\s+|(?:\s*;\s*)|(?:\s*,\s*)', lemma_txt) if s]


def differenz(lemma, variante):
    # finde den ersten Unterschied von links
    l = 0
    while l < min(len(lemma), len(variante)) and lemma[l] == variante[l]:
        l += 1

    # finde den ersten Unterschied von rechts
    r = 1
    while r <= min(len(lemma), len(variante)) and lemma[-r] == variante[-r]:
        r += 1
    r -= 1

    l -= 1              # beginne 1 Zeichen vor dem ersten Unterschied
    if l <= 1:  l = 0   # einzelne Buchstaben nicht abtrennen

    r -= 1              # beginne 1 Zeichen nach dem letzten Unterschied
    if r <= 1:  r = 0   # einzelne Buchstaben nicht abtrennen

    # gib Zeichenkette der Unterschide ab dem letzten gemeinsamen (von links) bzw.
    # ab dem ersten gemeinsamen (von rechts) Buchstaben mit Trennstrichen zurück
    return (('-' if l > 0 else '') + variante[l:(-r) or None] + ('-' if r > 0 else ''))


def verdichtung_lemmavarianten(lemma_txt):
    geteilt = teile_lemma(lemma_txt)
    lemma = geteilt[0]
    varianten = geteilt[1:]
    for v in varianten:
        print(differenz(lemma, v))


if __name__ == "__main__":
    verdichtung_lemmavarianten(testfall_facitergula)
