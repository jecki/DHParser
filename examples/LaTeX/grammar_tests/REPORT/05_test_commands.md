

Test of parser: "command"
=========================


Match-test "1"
--------------

### Test-code:
    \includegraphics[width=\textwidth]{Graph.eps}

### AST
    (command
        (known_command
            (includegraphics
                (:Token
                    (:RegExp
                        "\includegraphics"
                    )
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
                    (text_element
                        (text
                            "Graph.eps"
                        )
                    )
                )
            )
        )
    )

Match-test "2"
--------------

### Test-code:
    \multicolumn{1}{c}{ }

### AST
    (command
        (known_command
            (multicolumn
                (:Token
                    (:RegExp
                        "\multicolumn"
                    )
                )
                (:Token
                    (:RegExp
                        "{"
                    )
                )
                (INTEGER
                    "1"
                )
                (:Token
                    (:RegExp
                        "}"
                    )
                )
                (tabular_config
                    (:Token
                        (:RegExp
                            "{"
                        )
                    )
                    (:RegExp
                        "c"
                    )
                    (:Token
                        (:RegExp
                            "}"
                        )
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
                        (:RegExp
                            "}"
                        )
                    )
                )
            )
        )
    )

Match-test "3"
--------------

### Test-code:
    \multicolumn{2}{c|}{material}

### AST
    (command
        (known_command
            (multicolumn
                (:Token
                    (:RegExp
                        "\multicolumn"
                    )
                )
                (:Token
                    (:RegExp
                        "{"
                    )
                )
                (INTEGER
                    "2"
                )
                (:Token
                    (:RegExp
                        "}"
                    )
                )
                (tabular_config
                    (:Token
                        (:RegExp
                            "{"
                        )
                    )
                    (:RegExp
                        "c|"
                    )
                    (:Token
                        (:RegExp
                            "}"
                        )
                    )
                )
                (block_of_paragraphs
                    (:Token
                        (:RegExp
                            "{"
                        )
                    )
                    (sequence
                        (paragraph
                            (text_element
                                (text
                                    "material"
                                )
                            )
                        )
                    )
                    (:Token
                        (:RegExp
                            "}"
                        )
                    )
                )
            )
        )
    )

Match-test "4"
--------------

### Test-code:
    \multicolumn{2}{c}{$\underbrace{\hspace{7cm}}_{Simulations}$}

### AST
    (command
        (known_command
            (multicolumn
                (:Token
                    (:RegExp
                        "\multicolumn"
                    )
                )
                (:Token
                    (:RegExp
                        "{"
                    )
                )
                (INTEGER
                    "2"
                )
                (:Token
                    (:RegExp
                        "}"
                    )
                )
                (tabular_config
                    (:Token
                        (:RegExp
                            "{"
                        )
                    )
                    (:RegExp
                        "c"
                    )
                    (:Token
                        (:RegExp
                            "}"
                        )
                    )
                )
                (block_of_paragraphs
                    (:Token
                        (:RegExp
                            "{"
                        )
                    )
                    (sequence
                        (paragraph
                            (text_element
                                (inline_math
                                    "\underbrace{\hspace{7cm}}_{Simulations}"
                                )
                            )
                        )
                    )
                    (:Token
                        (:RegExp
                            "}"
                        )
                    )
                )
            )
        )
    )