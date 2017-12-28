

Test of parser: "tabular"
=========================


Match-test "1"
--------------

### Test-code:
    \begin{tabular}{c|c|}
    & $S_1$ \\ \cline{1-2}
    $A_1$ & $r_1$ \\ \cline{1-2}
    $A_2$ & $r_2$ \\ \cline{1-2}
    \end{tabular}

### AST
    (tabular
        (tabular_config
            (:RegExp
                "c|c|"
            )
            (:Whitespace
                " "
            )
        )
        (tabular_row
            (tabular_cell
                (inline_math
                    "S_1"
                )
            )
            (:Token
                "\\"
            )
            (cline
                (:Token
                    "\cline{"
                )
                (INTEGER
                    (:RegExp
                        "1"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (:Token
                    "-"
                )
                (INTEGER
                    (:RegExp
                        "2"
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
        (tabular_row
            (tabular_cell
                (inline_math
                    "A_1"
                )
            )
            (tabular_cell
                (inline_math
                    "r_1"
                )
            )
            (:Token
                "\\"
            )
            (cline
                (:Token
                    "\cline{"
                )
                (INTEGER
                    (:RegExp
                        "1"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (:Token
                    "-"
                )
                (INTEGER
                    (:RegExp
                        "2"
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
        (tabular_row
            (tabular_cell
                (inline_math
                    "A_2"
                )
            )
            (tabular_cell
                (inline_math
                    "r_2"
                )
            )
            (:Token
                "\\"
            )
            (cline
                (:Token
                    "\cline{"
                )
                (INTEGER
                    (:RegExp
                        "1"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (:Token
                    "-"
                )
                (INTEGER
                    (:RegExp
                        "2"
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
    )

Match-test "2"
--------------

### Test-code:
    \begin{tabular}{c|c|c|c|cc|c|c|c|}
    \multicolumn{1}{c}{} & \multicolumn{3}{c}{Tabelle 1:} &
    \multicolumn{2}{c}{} & \multicolumn{3}{c}{Tabelle 2:}
    \\
    \cline{2-4} \cline{7-9}
    $A_1$ &  7 &  0 &  4  & & $A_1$ &  5 & 20 &  6  \\
    \cline{2-4} \cline{7-9}
    $A_2$ &  5 & 21 & 11  & & $A_2$ & -3 &  8 & 10  \\
    \cline{2-4} \cline{7-9}
    $A_3$ & 10 & -5 & -1  & & $A_3$ &  4 &  5 &  9  \\
    \cline{2-4} \cline{7-9}
    \end{tabular}

### AST
    (tabular
        (tabular_config
            (:RegExp
                "c|c|c|c|cc|c|c|c|"
            )
            (:Whitespace
                " "
            )
        )
        (tabular_row
            (multicolumn
                (INTEGER
                    (:RegExp
                        "1"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (tabular_config
                    (:RegExp
                        "c"
                    )
                    (:Whitespace
                        " "
                    )
                )
            )
            (multicolumn
                (INTEGER
                    (:RegExp
                        "3"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (tabular_config
                    (:RegExp
                        "c"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (block_of_paragraphs
                    (text
                        "Tabelle 1:"
                    )
                    (:Whitespace
                        " "
                    )
                )
            )
            (multicolumn
                (INTEGER
                    (:RegExp
                        "2"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (tabular_config
                    (:RegExp
                        "c"
                    )
                    (:Whitespace
                        " "
                    )
                )
            )
            (multicolumn
                (INTEGER
                    (:RegExp
                        "3"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (tabular_config
                    (:RegExp
                        "c"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (block_of_paragraphs
                    (text
                        "Tabelle 2:"
                    )
                    (:Whitespace
                        " "
                    )
                )
            )
            (:Token
                "\\"
            )
            (cline
                (:Token
                    "\cline{"
                )
                (INTEGER
                    (:RegExp
                        "2"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (:Token
                    "-"
                )
                (INTEGER
                    (:RegExp
                        "4"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (:Token
                    "}"
                )
            )
            (cline
                (:Token
                    "\cline{"
                )
                (INTEGER
                    (:RegExp
                        "7"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (:Token
                    "-"
                )
                (INTEGER
                    (:RegExp
                        "9"
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
        (tabular_row
            (tabular_cell
                (inline_math
                    "A_1"
                )
            )
            (tabular_cell
                (text
                    "7"
                )
            )
            (tabular_cell
                (text
                    "0"
                )
            )
            (tabular_cell
                (text
                    "4"
                )
            )
            (tabular_cell
                (inline_math
                    "A_1"
                )
            )
            (tabular_cell
                (text
                    "5"
                )
            )
            (tabular_cell
                (text
                    "20"
                )
            )
            (tabular_cell
                (text
                    "6"
                )
            )
            (:Token
                "\\"
            )
            (cline
                (:Token
                    "\cline{"
                )
                (INTEGER
                    (:RegExp
                        "2"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (:Token
                    "-"
                )
                (INTEGER
                    (:RegExp
                        "4"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (:Token
                    "}"
                )
            )
            (cline
                (:Token
                    "\cline{"
                )
                (INTEGER
                    (:RegExp
                        "7"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (:Token
                    "-"
                )
                (INTEGER
                    (:RegExp
                        "9"
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
        (tabular_row
            (tabular_cell
                (inline_math
                    "A_2"
                )
            )
            (tabular_cell
                (text
                    "5"
                )
            )
            (tabular_cell
                (text
                    "21"
                )
            )
            (tabular_cell
                (text
                    "11"
                )
            )
            (tabular_cell
                (inline_math
                    "A_2"
                )
            )
            (tabular_cell
                (text
                    "-3"
                )
            )
            (tabular_cell
                (text
                    "8"
                )
            )
            (tabular_cell
                (text
                    "10"
                )
            )
            (:Token
                "\\"
            )
            (cline
                (:Token
                    "\cline{"
                )
                (INTEGER
                    (:RegExp
                        "2"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (:Token
                    "-"
                )
                (INTEGER
                    (:RegExp
                        "4"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (:Token
                    "}"
                )
            )
            (cline
                (:Token
                    "\cline{"
                )
                (INTEGER
                    (:RegExp
                        "7"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (:Token
                    "-"
                )
                (INTEGER
                    (:RegExp
                        "9"
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
        (tabular_row
            (tabular_cell
                (inline_math
                    "A_3"
                )
            )
            (tabular_cell
                (text
                    "10"
                )
            )
            (tabular_cell
                (text
                    "-5"
                )
            )
            (tabular_cell
                (text
                    "-1"
                )
            )
            (tabular_cell
                (inline_math
                    "A_3"
                )
            )
            (tabular_cell
                (text
                    "4"
                )
            )
            (tabular_cell
                (text
                    "5"
                )
            )
            (tabular_cell
                (text
                    "9"
                )
            )
            (:Token
                "\\"
            )
            (cline
                (:Token
                    "\cline{"
                )
                (INTEGER
                    (:RegExp
                        "2"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (:Token
                    "-"
                )
                (INTEGER
                    (:RegExp
                        "4"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (:Token
                    "}"
                )
            )
            (cline
                (:Token
                    "\cline{"
                )
                (INTEGER
                    (:RegExp
                        "7"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (:Token
                    "-"
                )
                (INTEGER
                    (:RegExp
                        "9"
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
    )


Test of parser: "figure"
========================


Match-test "1"
--------------

### Test-code:
    \begin{figure}
    \doublespacing
    \begin{center}
    \begin{tabular}{l|c|c|c|}
    \multicolumn{1}{c}{ } & \multicolumn{1}{c}{ } & \multicolumn{2}{c}{$\overbrace{\hspace{7cm}}^{Experiments}$} \\ \cline{2-4}
    & {\bf computer simulation} & {\bf analog simulation} & {\bf plain experiment} \\ \hline
    materiality of object
    & semantic              & \multicolumn{2}{c|}{material} \\ \hline
    relation to target
    & \multicolumn{2}{c|}{representation}       & representative \\ \hline
    \multicolumn{1}{c}{ } & \multicolumn{2}{c}{$\underbrace{\hspace{7cm}}_{Simulations}$} & \multicolumn{1}{c}{ } \\
    \end{tabular}
    \end{center}
    \caption{Conceptual relation of simulations and experiments}\label{SimulationExperimentsScheme}
    \end{figure}

### AST
    (figure
        (paragraph
            (generic_command
                (CMDNAME
                    "\doublespacing"
                )
            )
            (:Whitespace
                " "
            )
        )
        (generic_block
            (begin_environment
                "center"
            )
            (tabular
                (tabular_config
                    (:RegExp
                        "l|c|c|c|"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (tabular_row
                    (multicolumn
                        (INTEGER
                            (:RegExp
                                "1"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                        (tabular_config
                            (:RegExp
                                "c"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                    )
                    (multicolumn
                        (INTEGER
                            (:RegExp
                                "1"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                        (tabular_config
                            (:RegExp
                                "c"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                    )
                    (multicolumn
                        (INTEGER
                            (:RegExp
                                "2"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                        (tabular_config
                            (:RegExp
                                "c"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                        (block_of_paragraphs
                            (inline_math
                                "\overbrace{\hspace{7cm}}^{Experiments}"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                    )
                    (:Token
                        "\\"
                    )
                    (cline
                        (:Token
                            "\cline{"
                        )
                        (INTEGER
                            (:RegExp
                                "2"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                        (:Token
                            "-"
                        )
                        (INTEGER
                            (:RegExp
                                "4"
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
                (tabular_row
                    (tabular_cell
                        (block
                            (:Whitespace
                                " "
                            )
                            (generic_command
                                (CMDNAME
                                    "\bf"
                                )
                            )
                            (:Whitespace
                                " "
                            )
                            (text
                                "computer simulation"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                    )
                    (tabular_cell
                        (block
                            (:Whitespace
                                " "
                            )
                            (generic_command
                                (CMDNAME
                                    "\bf"
                                )
                            )
                            (:Whitespace
                                " "
                            )
                            (text
                                "analog simulation"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                    )
                    (tabular_cell
                        (block
                            (:Whitespace
                                " "
                            )
                            (generic_command
                                (CMDNAME
                                    "\bf"
                                )
                            )
                            (:Whitespace
                                " "
                            )
                            (text
                                "plain experiment"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                    )
                    (:Token
                        "\\"
                    )
                    (hline
                        "\hline"
                    )
                )
                (tabular_row
                    (tabular_cell
                        (text
                            "materiality of object"
                        )
                    )
                    (tabular_cell
                        (text
                            "semantic"
                        )
                    )
                    (multicolumn
                        (INTEGER
                            (:RegExp
                                "2"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                        (tabular_config
                            (:RegExp
                                "c|"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                        (block_of_paragraphs
                            (text
                                "material"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                    )
                    (:Token
                        "\\"
                    )
                    (hline
                        "\hline"
                    )
                )
                (tabular_row
                    (tabular_cell
                        (text
                            "relation to target"
                        )
                    )
                    (multicolumn
                        (INTEGER
                            (:RegExp
                                "2"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                        (tabular_config
                            (:RegExp
                                "c|"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                        (block_of_paragraphs
                            (text
                                "representation"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                    )
                    (tabular_cell
                        (text
                            "representative"
                        )
                    )
                    (:Token
                        "\\"
                    )
                    (hline
                        "\hline"
                    )
                )
                (tabular_row
                    (multicolumn
                        (INTEGER
                            (:RegExp
                                "1"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                        (tabular_config
                            (:RegExp
                                "c"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                    )
                    (multicolumn
                        (INTEGER
                            (:RegExp
                                "2"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                        (tabular_config
                            (:RegExp
                                "c"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                        (block_of_paragraphs
                            (inline_math
                                "\underbrace{\hspace{7cm}}_{Simulations}"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                    )
                    (multicolumn
                        (INTEGER
                            (:RegExp
                                "1"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                        (tabular_config
                            (:RegExp
                                "c"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                    )
                    (:Token
                        "\\"
                    )
                )
            )
            (end_environment
                "center"
            )
        )
        (paragraph
            (caption
                (block
                    (:Whitespace
                        " "
                    )
                    (text
                        "Conceptual relation of simulations and experiments"
                    )
                    (:Whitespace
                        " "
                    )
                )
            )
            (:Whitespace
                " "
            )
            (generic_command
                (CMDNAME
                    "\label"
                )
                (:Whitespace
                    " "
                )
                (block
                    (:Whitespace
                        " "
                    )
                    (text
                        "SimulationExperimentsScheme"
                    )
                    (:Whitespace
                        " "
                    )
                )
            )
            (:Whitespace
                ""
                ""
            )
        )
    )