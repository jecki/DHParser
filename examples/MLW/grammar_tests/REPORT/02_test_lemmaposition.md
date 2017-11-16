

Test of parser: "Lemma"
=======================


Match-test "1"
--------------

### Test-code:
    facitergula

### AST
    (Lemma
        (LemmaWort
            (LAT_WORT
                (:RegExp
                    "facitergula"
                )
            )
        )
    )

Match-test "2"
--------------

### Test-code:
    facitergul|a

### Error:
Match test "2" for parser "Lemma" failed:
	Expr.:  facitergul|a

	line:   1, column: 11, Error: Parser stopped before end! trying to recover but stopping history recording at this point.
	line:   1, column: 11, Error: Parser did not match! Invalid source file?
		    Most advanced: line 1, column 11:  Lemma->LemmaWort->LAT_WORT->/[a-z]+/  "facitergul"
		    Last match:    line 1, column 11:  Lemma->LemmaWort->LAT_WORT->:Whitespace  "";



### AST
    (__ZOMBIE__
        (Lemma
            (LemmaWort
                (LAT_WORT
                    (:RegExp
                        "facitergul"
                    )
                )
            )
        )
        (__ZOMBIE__
            "|a"
        )
    )

Match-test "3"
--------------

### Test-code:
    fasc|itergula

### Error:
Match test "3" for parser "Lemma" failed:
	Expr.:  fasc|itergula

	line:   1, column:  5, Error: Parser stopped before end! trying to recover but stopping history recording at this point.



### AST
    (__ZOMBIE__
        (Lemma
            (LemmaWort
                (LAT_WORT
                    (:RegExp
                        "fasc"
                    )
                )
            )
        )
        (__ZOMBIE__
            "|iter"
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
    
    fasc-itergula
    fac-iet-ergula
    fac-ist-ergula
    fa-rcu-tergula
    

### AST
    (LemmaVarianten
        (LZ
            ""
            ""
        )
        (:OneOrMore
            (:Series
                (LemmaVariante
                    (LAT_WORT_TEIL
                        "fasc"
                    )
                    (:Series
                        (:Token
                            "-"
                        )
                        (LAT_WORT_TEIL
                            "itergula"
                        )
                    )
                )
                (ZWW
                    (ZEILENSPRUNG
                        (:RegExp
                            ""
                            ""
                        )
                    )
                )
            )
            (:Series
                (LemmaVariante
                    (LAT_WORT_TEIL
                        "fac"
                    )
                    (:ZeroOrMore
                        (:Series
                            (:Token
                                "-"
                            )
                            (LAT_WORT_TEIL
                                "iet"
                            )
                        )
                        (:Series
                            (:Token
                                "-"
                            )
                            (LAT_WORT_TEIL
                                "ergula"
                            )
                        )
                    )
                )
                (ZWW
                    (ZEILENSPRUNG
                        (:RegExp
                            ""
                            ""
                        )
                    )
                )
            )
            (:Series
                (LemmaVariante
                    (LAT_WORT_TEIL
                        "fac"
                    )
                    (:ZeroOrMore
                        (:Series
                            (:Token
                                "-"
                            )
                            (LAT_WORT_TEIL
                                "ist"
                            )
                        )
                        (:Series
                            (:Token
                                "-"
                            )
                            (LAT_WORT_TEIL
                                "ergula"
                            )
                        )
                    )
                )
                (ZWW
                    (ZEILENSPRUNG
                        (:RegExp
                            ""
                            ""
                        )
                    )
                )
            )
            (:Series
                (LemmaVariante
                    (LAT_WORT_TEIL
                        "fa"
                    )
                    (:ZeroOrMore
                        (:Series
                            (:Token
                                "-"
                            )
                            (LAT_WORT_TEIL
                                "rcu"
                            )
                        )
                        (:Series
                            (:Token
                                "-"
                            )
                            (LAT_WORT_TEIL
                                "tergula"
                            )
                        )
                    )
                )
                (ZWW
                    (ZEILENSPRUNG
                        (:RegExp
                            ""
                            ""
                        )
                    )
                )
            )
        )
    )

Match-test "2"
--------------

### Test-code:
     fasc-itergula;

### AST
    (LemmaVarianten
        (LZ
            " "
        )
        (:Series
            (LemmaVariante
                (LAT_WORT_TEIL
                    "fasc"
                )
                (:Series
                    (:Token
                        "-"
                    )
                    (LAT_WORT_TEIL
                        "itergula"
                    )
                )
            )
            (ABS
                ";"
            )
        )
    )

Match-test "3"
--------------

### Test-code:
     fasc-itergula fac-iet-ergula ZUSATZ sim.
    

### AST
    (LemmaVarianten
        (LZ
            " "
        )
        (:OneOrMore
            (:Series
                (LemmaVariante
                    (LAT_WORT_TEIL
                        "fasc"
                    )
                    (:Series
                        (:Token
                            "-"
                        )
                        (LAT_WORT_TEIL
                            "itergula"
                        )
                    )
                )
                (LZ
                    " "
                )
            )
            (:Series
                (LemmaVariante
                    (LAT_WORT_TEIL
                        "fac"
                    )
                    (:ZeroOrMore
                        (:Series
                            (:Token
                                "-"
                            )
                            (LAT_WORT_TEIL
                                "iet"
                            )
                        )
                        (:Series
                            (:Token
                                "-"
                            )
                            (LAT_WORT_TEIL
                                "ergula"
                            )
                        )
                    )
                )
                (LZ
                    " "
                )
            )
        )
        (Zusatz
            (:Token
                (:RegExp
                    "ZUSATZ"
                )
                (:Whitespace
                    " "
                )
            )
            (:Series
                (zusatz_typ
                    "sim."
                )
                (ZWW
                    (ZEILENSPRUNG
                        (:RegExp
                            ""
                            ""
                        )
                    )
                )
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
    LEMMA facitergul|a
    
    fasc-itergula
    fac-iet-ergula
    fac-ist-ergula
    fascite-rcu-la
    
    ZUSATZ sim.
    
    GRAMMATIK
    nomen; -ae f.
    

### Error:
Match test "1" for parser "LemmaPosition" failed:
	Expr.:  LEMMA facitergul|a
	
	fasc-itergula
	fac-iet-ergula
	fac-ist-ergula
	fascite-rcu-la
	
	ZUSATZ sim.
	
	GRAMMATIK
	nomen; -ae f.
	

	line:   1, column: 17, Error: TR = (ABS | LZ) expected; "|a
		
		fasc-i" found!
	line:  11, column: 12, Error: "," expected; "f.
		" found!
	line:  12, column:  1, Error: FLEX = /-?[a-z]+/~ expected; "" found!
	line:  12, column:  1, Error: ABS = (/\s*;;?\s*/ | {ZWW}+) expected; "" found!



### AST
    (LemmaPosition
        (:Token
            (:RegExp
                "LEMMA"
            )
            (:Whitespace
                " "
            )
        )
        (Lemma
            (LemmaWort
                (LAT_WORT
                    (:RegExp
                        "facitergul"
                    )
                )
            )
        )
        (LemmaPosition
            "|a"
            ""
            "fa"
        )
        (LemmaVarianten
            (:OneOrMore
                (:Series
                    (LemmaVariante
                        (LAT_WORT_TEIL
                            "sc"
                        )
                        (:Series
                            (:Token
                                "-"
                            )
                            (LAT_WORT_TEIL
                                "itergula"
                            )
                        )
                    )
                    (ZWW
                        (ZEILENSPRUNG
                            (:RegExp
                                ""
                                ""
                            )
                        )
                    )
                )
                (:Series
                    (LemmaVariante
                        (LAT_WORT_TEIL
                            "fac"
                        )
                        (:ZeroOrMore
                            (:Series
                                (:Token
                                    "-"
                                )
                                (LAT_WORT_TEIL
                                    "iet"
                                )
                            )
                            (:Series
                                (:Token
                                    "-"
                                )
                                (LAT_WORT_TEIL
                                    "ergula"
                                )
                            )
                        )
                    )
                    (ZWW
                        (ZEILENSPRUNG
                            (:RegExp
                                ""
                                ""
                            )
                        )
                    )
                )
                (:Series
                    (LemmaVariante
                        (LAT_WORT_TEIL
                            "fac"
                        )
                        (:ZeroOrMore
                            (:Series
                                (:Token
                                    "-"
                                )
                                (LAT_WORT_TEIL
                                    "ist"
                                )
                            )
                            (:Series
                                (:Token
                                    "-"
                                )
                                (LAT_WORT_TEIL
                                    "ergula"
                                )
                            )
                        )
                    )
                    (ZWW
                        (ZEILENSPRUNG
                            (:RegExp
                                ""
                                ""
                            )
                        )
                    )
                )
                (:Series
                    (LemmaVariante
                        (LAT_WORT_TEIL
                            "fascite"
                        )
                        (:ZeroOrMore
                            (:Series
                                (:Token
                                    "-"
                                )
                                (LAT_WORT_TEIL
                                    "rcu"
                                )
                            )
                            (:Series
                                (:Token
                                    "-"
                                )
                                (LAT_WORT_TEIL
                                    "la"
                                )
                            )
                        )
                    )
                    (ZWW
                        (ZEILENSPRUNG
                            (:RegExp
                                ""
                                ""
                            )
                        )
                        (LEERRAUM
                            (:RegExp
                                ""
                                ""
                            )
                        )
                    )
                )
            )
            (Zusatz
                (:Token
                    (:RegExp
                        "ZUSATZ"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (:Series
                    (zusatz_typ
                        "sim."
                    )
                    (ZWW
                        (ZEILENSPRUNG
                            (:RegExp
                                ""
                                ""
                            )
                        )
                        (LEERRAUM
                            (:RegExp
                                ""
                                ""
                            )
                        )
                    )
                )
            )
        )
        (GrammatikPosition
            (:Token
                "GRAMMATIK"
            )
            (LZ
                ""
                ""
            )
            (Grammatik
                (wortart
                    "nomen"
                )
                (ABS
                    "; "
                )
                (flexion
                    (deklination
                        (FLEX
                            (:RegExp
                                "-ae"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                        (deklination
                            "f."
                            ""
                        )
                    )
                )
            )
        )
    )