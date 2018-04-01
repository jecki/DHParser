

Test of parser: "paragraph"
===========================


Match-test "1"
--------------

### Test-code:
    Im allgemeinen werden die Bewohner Göttingens eingeteilt in Studenten,
    Professoren, Philister und Vieh; welche vier Stände doch nichts weniger
    als streng geschieden sind. Der Viehstand ist der bedeutendste.

### AST
    (paragraph
        (text
            "Im allgemeinen werden die Bewohner Göttingens eingeteilt in Studenten,"
            "Professoren, Philister und Vieh; welche vier Stände doch nichts weniger"
            "als streng geschieden sind. Der Viehstand ist der bedeutendste."
        )
    )

Match-test "2"
--------------

### Test-code:
    Paragraphs may contain {\em inline blocks} as well as \emph{inline commands}
    and also special \& characters.

### AST
    (paragraph
        (text
            "Paragraphs may contain"
        )
        (:Whitespace
            " "
        )
        (block
            (generic_command
                (CMDNAME
                    "\em"
                )
            )
            (text
                "inline blocks"
            )
        )
        (:Whitespace
            " "
        )
        (text
            "as well as"
        )
        (:Whitespace
            " "
        )
        (generic_command
            (CMDNAME
                "\emph"
            )
            (text
                "inline commands"
            )
        )
        (:Whitespace
            ""
            ""
        )
        (text
            "and also special"
        )
        (:Whitespace
            " "
        )
        (text_command
            (ESCAPED
                "&"
            )
        )
        (:Whitespace
            " "
        )
        (text
            "characters."
        )
    )

Match-test "3"
--------------

### Test-code:
    Paragraphs are separated only by at least one blank line.
    Therefore,
                 this line still belongs to the same paragraph.

### AST
    (paragraph
        (text
            "Paragraphs are separated only by at least one blank line."
            "Therefore,"
            "this line still belongs to the same paragraph."
        )
    )

Match-test "4"
--------------

### Test-code:
    Paragraphs   % may contain comments
    like the comment above
    % or like thist comment.
    Comment lines do not break paragraphs.
    % There can even be several comment lines,
        % even indented comment lines,
    in sequence.

### AST
    (paragraph
        (text
            "Paragraphs"
            "like the comment above"
            "Comment lines do not break paragraphs."
            "in sequence."
        )
    )

Match-test "5"
--------------

### Test-code:
    Paragraphs may contain {\em emphasized} or {\bf bold} text.
    Most of these commands can have different forms as, for example:
    \begin{small} small \end{small} or {\large large}.

### AST
    (paragraph
        (text
            "Paragraphs may contain"
        )
        (:Whitespace
            " "
        )
        (block
            (generic_command
                (CMDNAME
                    "\em"
                )
            )
            (text
                "emphasized"
            )
        )
        (:Whitespace
            " "
        )
        (text
            "or"
        )
        (:Whitespace
            " "
        )
        (block
            (generic_command
                (CMDNAME
                    "\bf"
                )
            )
            (text
                "bold"
            )
        )
        (:Whitespace
            " "
        )
        (text
            "text."
            "Most of these commands can have different forms as, for example:"
        )
        (:Whitespace
            ""
            ""
        )
        (generic_inline_env
            (begin_environment
                "small"
            )
            (:Whitespace
                " "
            )
            (paragraph
                (text
                    "small"
                )
                (:Whitespace
                    " "
                )
            )
            (end_environment
                "small"
            )
        )
        (:Whitespace
            " "
        )
        (text
            "or"
        )
        (:Whitespace
            " "
        )
        (block
            (generic_command
                (CMDNAME
                    "\large"
                )
            )
            (text
                "large"
            )
        )
        (text
            "."
        )
    )

Match-test "6"
--------------

### Test-code:
    Paragraphs may also contain {\xy unknown blocks }.

### AST
    (paragraph
        (text
            "Paragraphs may also contain"
        )
        (:Whitespace
            " "
        )
        (block
            (generic_command
                (CMDNAME
                    "\xy"
                )
            )
            (text
                "unknown blocks"
            )
            (:Whitespace
                " "
            )
        )
        (text
            "."
        )
    )

Match-test "7"
--------------

### Test-code:
    Paragraphs may contain \xy[xycgf]{some {\em unbknown}} commands.

### AST
    (paragraph
        (text
            "Paragraphs may contain"
        )
        (:Whitespace
            " "
        )
        (generic_command
            (CMDNAME
                "\xy"
            )
            (config
                "xycgf"
            )
            (block
                (text
                    "some"
                )
                (:Whitespace
                    " "
                )
                (block
                    (generic_command
                        (CMDNAME
                            "\em"
                        )
                    )
                    (text
                        "unbknown"
                    )
                )
            )
        )
        (:Whitespace
            " "
        )
        (text
            "commands."
        )
    )

Match-test "8"
--------------

### Test-code:
    Unknwon \xy commands within paragraphs may be simple
    or \xy{complex}.

### AST
    (paragraph
        (text
            "Unknwon"
        )
        (:Whitespace
            " "
        )
        (generic_command
            (CMDNAME
                "\xy"
            )
        )
        (text
            "commands within paragraphs may be simple"
            "or"
        )
        (:Whitespace
            " "
        )
        (generic_command
            (CMDNAME
                "\xy"
            )
            (text
                "complex"
            )
        )
        (text
            "."
        )
    )

Match-test "9"
--------------

### Test-code:
    paragraphs may contain all of these: \{ escaped \} characters,
    {\bf blocks}, [ brackets ], \begin{tiny} environments \end{tiny}
    and \textbackslash text-commands or other commands like this
    \footnote{footnote}

### AST
    (paragraph
        (text
            "paragraphs may contain all of these:"
        )
        (:Whitespace
            " "
        )
        (text_command
            (ESCAPED
                "{"
            )
        )
        (:Whitespace
            " "
        )
        (text
            "escaped"
        )
        (:Whitespace
            " "
        )
        (text_command
            (ESCAPED
                "}"
            )
        )
        (:Whitespace
            " "
        )
        (text
            "characters,"
        )
        (:Whitespace
            ""
            ""
        )
        (block
            (generic_command
                (CMDNAME
                    "\bf"
                )
            )
            (text
                "blocks"
            )
        )
        (text
            ","
        )
        (:Whitespace
            " "
        )
        (text_command
            (BRACKETS
                "["
            )
        )
        (:Whitespace
            " "
        )
        (text
            "brackets"
        )
        (:Whitespace
            " "
        )
        (text_command
            (BRACKETS
                "]"
            )
        )
        (text
            ","
        )
        (:Whitespace
            " "
        )
        (generic_inline_env
            (begin_environment
                "tiny"
            )
            (:Whitespace
                " "
            )
            (paragraph
                (text
                    "environments"
                )
                (:Whitespace
                    " "
                )
            )
            (end_environment
                "tiny"
            )
        )
        (:Whitespace
            ""
            ""
        )
        (text
            "and"
        )
        (:Whitespace
            " "
        )
        (text_command
            (TXTCOMMAND
                "\textbackslash"
            )
        )
        (:Whitespace
            " "
        )
        (text
            "text-commands or other commands like this"
        )
        (:Whitespace
            ""
            ""
        )
        (footnote
            (block_of_paragraphs
                (text
                    "footnote"
                )
            )
        )
    )

Match-test "10"
---------------

### Test-code:
    \begin{generic}inline environment\end{generic}
    

### AST
    (paragraph
        (generic_inline_env
            (begin_environment
                "generic"
            )
            (paragraph
                (text
                    "inline environment"
                )
            )
            (end_environment
                "generic"
            )
        )
        (:Whitespace
            ""
            ""
        )
    )

Match-test "11"
---------------

### Test-code:
    \begin{generic}inline environment
    \end{generic}
    

### AST
    (paragraph
        (generic_inline_env
            (begin_environment
                "generic"
            )
            (paragraph
                (text
                    "inline environment"
                )
                (:Whitespace
                    ""
                    ""
                )
            )
            (end_environment
                "generic"
            )
        )
        (:Whitespace
            ""
            ""
        )
    )

Fail-test "20"
--------------

### Test-code:
    Paragraphs are separated by gaps.
    
        Like this one.

Fail-test "21"
--------------

### Test-code:
    \begin{enumerate}

Fail-test "22"
--------------

### Test-code:
    \item

Fail-test "23"
--------------

### Test-code:
    und Vieh; \paragraph

Fail-test "24"
--------------

### Test-code:
    Paragraphs will end
    \begin{quotation}
    at block environments
    \end{quotation}
    like block quotes.


Test of parser: "sequence"
==========================


Match-test "1"
--------------

### Test-code:
    Paragraphs are separated by gaps.
    
        Like this one.

### AST
    (sequence
        (paragraph
            (text
                "Paragraphs are separated by gaps."
            )
        )
        (paragraph
            (text
                "Like this one."
            )
        )
    )

Match-test "2"
--------------

### Test-code:
    The second paragraph follows after a long gap.
    
    
        The parser should accept this, too.

### AST
    (sequence
        (paragraph
            (text
                "The second paragraph follows after a long gap."
            )
        )
        (paragraph
            (text
                "The parser should accept this, too."
            )
        )
    )

Match-test "3"
--------------

### Test-code:
    Paragraphs can be delimited by  % comment
    
        % sequences of separators
    
        % and comments
        % or sequences of comment lines
    
        In the end such a sequence counts
        % merely as one comment

### AST
    (sequence
        (paragraph
            (text
                "Paragraphs can be delimited by"
            )
            (:Whitespace
                ""
                ""
            )
        )
        (paragraph
            (text
                "In the end such a sequence counts"
            )
            (:Whitespace
                ""
                ""
            )
        )
    )

Match-test "4"
--------------

### Test-code:
    Sequences of paragraphs may
    \begin{quotation}
    include block environments
    \end{quotation}
    like block quotes.

### AST
    (sequence
        (paragraph
            (text
                "Sequences of paragraphs may"
            )
            (:Whitespace
                ""
                ""
            )
        )
        (quotation
            (paragraph
                (text
                    "include block environments"
                )
                (:Whitespace
                    ""
                    ""
                )
            )
        )
        (paragraph
            (text
                "like block quotes."
            )
        )
    )