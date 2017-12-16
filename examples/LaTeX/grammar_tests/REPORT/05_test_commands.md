

Test of parser: "command"
=========================


Match-test "1"
--------------

### Test-code:
    \includegraphics[width=\textwidth]{Graph.eps}

### AST
    (includegraphics
        (config
            (text
                "width="
            )
            (CMDNAME
                "\textwidth"
            )
        )
        (text
            "Graph.eps"
        )
    )

Match-test "2"
--------------

### Test-code:
    \multicolumn{1}{c}{ }

### AST
    (multicolumn
        (INTEGER
            "1"
        )
        (tabular_config
            "c"
        )
    )

Match-test "3"
--------------

### Test-code:
    \multicolumn{2}{c|}{material}

### AST
    (multicolumn
        (INTEGER
            "2"
        )
        (tabular_config
            "c|"
        )
        (block_of_paragraphs
            (text
                "material"
            )
        )
    )

Match-test "4"
--------------

### Test-code:
    \multicolumn{2}{c}{$\underbrace{\hspace{7cm}}_{Simulations}$}

### AST
    (multicolumn
        (INTEGER
            "2"
        )
        (tabular_config
            "c"
        )
        (block_of_paragraphs
            (inline_math
                "\underbrace{\hspace{7cm}}_{Simulations}"
            )
        )
    )