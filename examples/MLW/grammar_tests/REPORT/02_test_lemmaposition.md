

Test of parser: "Lemma"
=======================


Match-test "1"
--------------

### Test-code:
    facitergula

### AST
    (Lemma
        (LemmaWort
            "facitergula"
        )
    )

Fail-test "99"
--------------

### Test-code:
    duo vocabula


Test of parser: "LemmaVarianten"
================================


Match-test "1"
--------------

### Test-code:
    fascitergula
    facietergula
    facistergula
    farcutergula

### AST
    (LemmaVarianten
        (LemmaVariante
            "fascitergula"
        )
        (LemmaVariante
            "facietergula"
        )
        (LemmaVariante
            "facistergula"
        )
        (LemmaVariante
            "farcutergula"
        )
    )

Match-test "2"
--------------

### Test-code:
    fascitergula

### AST
    (LemmaVarianten
        (LemmaVariante
            "fascitergula"
        )
    )

Match-test "3"
--------------

### Test-code:
    fascitergula facietergula {sim.}

### AST
    (LemmaVarianten
        (LemmaVariante
            (:RegExp
                "fascitergula"
            )
            (:Whitespace
                " "
            )
        )
        (LemmaVariante
            (LAT_WORT
                "facietergula"
            )
            (Zusatz
                "sim."
            )
        )
    )

Match-test "4"
--------------

### Test-code:
    fascitergula, facietergula, fascistergula {sim.}

### AST
    (LemmaVarianten
        (LemmaVariante
            "fascitergula"
        )
        (LemmaVariante
            "facietergula"
        )
        (LemmaVariante
            (LAT_WORT
                "fascistergula"
            )
            (Zusatz
                "sim."
            )
        )
    )

Fail-test "99"
--------------

### Test-code:
    * fascitergula


Test of parser: "LemmaPosition"
===============================


Match-test "1"
--------------

### Test-code:
    LEMMA facitergula
    
    fascitergula
    facietergula
    facistergula
    fascitercula {sim.}
    
    GRAMMATIK
    nomen; -ae f.

### AST
    (LemmaPosition
        (Lemma
            (LemmaWort
                "facitergula"
            )
        )
        (LemmaVarianten
            (LemmaVariante
                "fascitergula"
            )
            (LemmaVariante
                "facietergula"
            )
            (LemmaVariante
                "facistergula"
            )
            (LemmaVariante
                (LAT_WORT
                    "fascitercula"
                )
                (Zusatz
                    "sim."
                )
            )
        )
        (GrammatikPosition
            (Grammatik
                (nomen
                    "nomen"
                )
                (flexion
                    (deklination
                        (FLEX
                            "-ae"
                        )
                    )
                )
                (femininum
                    "femininum"
                )
            )
        )
    )