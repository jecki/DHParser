

Test of parser: "SCHLUESSELWORT"
================================


Match-test "M1"
---------------

### Test-code:
    
    AUTORIN 

### AST
    (SCHLUESSELWORT
        (:RegExp
            ""
            ""
        )
        (:RegExp
            "AUTORIN "
        )
    )


Test of parser: "RZS"
=====================


Match-test "M1"
---------------

### Test-code:
    
    

### CST
    (RZS
        ""
        ""
    )


Test of parser: "LEERZEILE"
===========================


Match-test "M1"
---------------

### Test-code:
    
    
        

### AST
    (LEERZEILE
        (:RegExp
            ""
            ""
            ""
        )
        (:RE
            "    "
        )
    )

Match-test "M2"
---------------

### Test-code:
    
    
        // Kommentar

### AST
    (LEERZEILE
        (:RegExp
            ""
            ""
            ""
        )
        (:RE
            "    // Kommentar"
        )
    )

Match-test "M3"
---------------

### Test-code:
    
    
    
        

### AST
    (LEERZEILE
        (:RegExp
            ""
            ""
            ""
            ""
        )
        (:RE
            "    "
        )
    )

Match-test "M4"
---------------

### Test-code:
    
    
        /* Kommentar
    
        Kommentar fortsetzung */

### AST
    (LEERZEILE
        (:RegExp
            ""
            ""
            ""
        )
        (:RE
            "    /* Kommentar"
            ""
            "    Kommentar fortsetzung */"
        )
    )

Fail-test "F1"
--------------

### Test-code:
    
    

Fail-test "F2"
--------------

### Test-code:
    
    
        // Kommentar
    
        // Kommentar
        


Test of parser: "LÜCKE"
=======================


Match-test "M1"
---------------

### Test-code:
    
    
        

### AST
    (LÜCKE
        (KOMMENTARZEILEN)
        (LEERZEILE
            (:RegExp
                ""
                ""
                ""
            )
            (:RE
                "    "
            )
        )
    )

Match-test "M2"
---------------

### Test-code:
    
    
        // Kommentar
        

### AST
    (LÜCKE
        (KOMMENTARZEILEN)
        (LEERZEILE
            (:RegExp
                ""
                ""
                ""
            )
            (:RE
                (:Whitespace
                    "    // Kommentar"
                )
                (:RegExp
                    ""
                    ""
                )
            )
        )
    )

Match-test "M3"
---------------

### Test-code:
    
    
    
        

### AST
    (LÜCKE
        (KOMMENTARZEILEN)
        (LEERZEILE
            (:RegExp
                ""
                ""
                ""
                ""
            )
            (:RE
                "    "
            )
        )
    )

Match-test "M4"
---------------

### Test-code:
    
    
        // Kommentar
    
        // Kommentar
        

### AST
    (LÜCKE
        (KOMMENTARZEILEN)
        (LEERZEILE
            (:RegExp
                ""
                ""
                ""
            )
            (:RE
                (:Whitespace
                    "    // Kommentar"
                )
                (:RegExp
                    ""
                    ""
                )
            )
        )
    )

Match-test "M5"
---------------

### Test-code:
     //Kommentar
        //Kommentar
    
        // Kommentar

### AST
    (LÜCKE
        (KOMMENTARZEILEN
            (:Series
                (:RegExp
                    " "
                )
                (:RegExp
                    "//Kommentar"
                )
            )
            (:Series
                (:RegExp
                    ""
                    "    "
                )
                (:RegExp
                    "//Kommentar"
                )
            )
        )
        (LEERZEILE
            (:RegExp
                ""
                ""
                ""
            )
            (:RE
                "    // Kommentar"
            )
        )
    )

Fail-test "F1"
--------------

### Test-code:
     

Fail-test "F2"
--------------

### Test-code:
    
    

Fail-test "F3"
--------------

### Test-code:
    
    // Kommentar

Fail-test "F4"
--------------

### Test-code:
     //Kommentar
    // Kommentar
    // Kommentar

Fail-test "F5"
--------------

### Test-code:
     //Kommentar
        /* Kommentar
    
           Kommentar */


Test of parser: "LZ"
====================


Match-test "M1"
---------------

### Test-code:
     

### AST
    (LZ
        (:RegExp
            " "
        )
    )

Match-test "M2"
---------------

### Test-code:
     // Kommentar

### AST
    (LZ
        (:RegExp
            " "
        )
        (:RegExp
            "// Kommentar"
        )
    )

Match-test "M3"
---------------

### Test-code:
      

### AST
    (LZ
        (:RegExp
            "  "
        )
    )

Match-test "M4"
---------------

### Test-code:
    // Kommentar

### AST
    (LZ
        (:RegExp
            "// Kommentar"
        )
    )

Match-test "M5"
---------------

### Test-code:
    // Kommentar
    

### AST
    (LZ
        (:RegExp
            "// Kommentar"
        )
        (:RegExp
            ""
            ""
        )
    )

Match-test "M6"
---------------

### Test-code:
    
        // Kommentar
    
        // Kommentar
    
        

### AST
    (LZ
        (:RegExp
            ""
            "    "
        )
        (:RegExp
            "// Kommentar"
        )
        (:RegExp
            ""
            ""
            "    "
        )
        (:RegExp
            "// Kommentar"
        )
        (:RegExp
            ""
            ""
            "    "
        )
    )

Match-test "M7"
---------------

### Test-code:
    
    
    
        

### AST
    (LZ
        (:RegExp
            ""
            ""
            ""
            "    "
        )
    )

Fail-test "F1"
--------------

### Test-code:
    X


Test of parser: "ZWW"
=====================


Match-test "M1"
---------------

### Test-code:
    
    

### AST
    (ZWW
        (ZEILENSPRUNG
            (:RegExp
                ""
                ""
            )
        )
    )

Match-test "M2"
---------------

### Test-code:
    
    // Kommentar

### AST
    (ZWW
        (ZEILENSPRUNG
            (:RegExp
                ""
                ""
            )
            (:Whitespace
                "// Kommentar"
            )
        )
    )

Match-test "M3"
---------------

### Test-code:
    
    // Kommentar
    

### AST
    (ZWW
        (ZEILENSPRUNG
            (:RegExp
                ""
                ""
            )
            (:Whitespace
                "// Kommentar"
            )
        )
    )

Match-test "M4"
---------------

### Test-code:
    
    
    
        

### AST
    (ZWW
        (ZEILENSPRUNG
            (:RegExp
                ""
                ""
            )
        )
    )

Fail-test "F1"
--------------

### Test-code:
     


Test of parser: "ZW"
====================


Match-test "M1"
---------------

### Test-code:
    
    

### AST
    (ZW
        (ZEILENSPRUNG
            (:RegExp
                ""
                ""
            )
        )
    )

Match-test "M2"
---------------

### Test-code:
    
    // Kommentar

### AST
    (ZW
        (ZEILENSPRUNG
            (:RegExp
                ""
                ""
            )
            (:Whitespace
                "// Kommentar"
            )
        )
    )

Fail-test "F1"
--------------

### Test-code:
    
    
        


Test of parser: "FREITEXT"
==========================


Fail-test "F1"
--------------

### Test-code:
    Text -> Verweis


Test of parser: "SEITENZAHL"
============================


Match-test "M1"
---------------

### Test-code:
    123

### AST
    (SEITENZAHL
        "123"
    )

Match-test "M2"
---------------

### Test-code:
    123^b

### AST
    (SEITENZAHL
        "123^b"
    )

Match-test "M3"
---------------

### Test-code:
    4^capit.

### AST
    (SEITENZAHL
        "4^capit."
    )

Match-test "M4"
---------------

### Test-code:
    4^{bona fide}

### AST
    (SEITENZAHL
        "4^{bona fide}"
    )

Fail-test "F1"
--------------

### Test-code:
    4^bona fide