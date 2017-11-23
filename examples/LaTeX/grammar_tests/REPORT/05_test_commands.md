

Test of parser: "command"
=========================


Match-test "1"
--------------

### Test-code:
    \includegraphics[width=\textwidth]{Graph.eps}

### AST
    (includegraphics
        (:Token
            "\includegraphics"
        )
        (config
            (cfg_text
                (text
                    "width="
                )
                (CMDNAME
                    "\textwidth"
                )
            )
        )
        (block
            (text
                "Graph.eps"
            )
        )
    )

Match-test "2"
--------------

### Test-code:
    \multicolumn{1}{c}{ }

### AST
    (multicolumn
        (:Token
            "\multicolumn"
        )
        (:Token
            "{"
        )
        (INTEGER
            "1"
        )
        (:Token
            "}"
        )
        (tabular_config
            (:Token
                "{"
            )
            (:RegExp
                "c"
            )
            (:Token
                "}"
            )
        )
        (block_of_paragraphs
            (:Token
                (:RegExp
                    "{"
                )
                (:Whitespace
                    " "
                )
            )
            (:Token
                "}"
            )
        )
    )

Match-test "3"
--------------

### Test-code:
    \multicolumn{2}{c|}{material}

### AST
    (multicolumn
        (:Token
            "\multicolumn"
        )
        (:Token
            "{"
        )
        (INTEGER
            "2"
        )
        (:Token
            "}"
        )
        (tabular_config
            (:Token
                "{"
            )
            (:RegExp
                "c|"
            )
            (:Token
                "}"
            )
        )
        (block_of_paragraphs
            (:Token
                "{"
            )
            (sequence
                (paragraph
                    (text
                        "material"
                    )
                )
            )
            (:Token
                "}"
            )
        )
    )

Match-test "4"
--------------

### Test-code:
    \multicolumn{2}{c}{$\underbrace{\hspace{7cm}}_{Simulations}$}

### AST
    (multicolumn
        (:Token
            "\multicolumn"
        )
        (:Token
            "{"
        )
        (INTEGER
            "2"
        )
        (:Token
            "}"
        )
        (tabular_config
            (:Token
                "{"
            )
            (:RegExp
                "c"
            )
            (:Token
                "}"
            )
        )
        (block_of_paragraphs
            (:Token
                "{"
            )
            (sequence
                (paragraph
                    (inline_math
                        "\underbrace{\hspace{7cm}}_{Simulations}"
                    )
                )
            )
            (:Token
                "}"
            )
        )
    )