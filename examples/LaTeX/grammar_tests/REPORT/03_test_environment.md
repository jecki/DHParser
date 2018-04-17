

Test of parser: "block_environment"
===================================


Match-test "1"
--------------

### Test-code:
    \begin{generic}
        A generic block element is a block element
        that is unknown to DHParser.
    
        Unknown begin-end-structures are always
        considered as block elements and not
        as inline elements.
        \end{generic}
        

### AST
    (generic_block
        (begin_environment
            "generic"
        )
        (paragraph
            (text
                "A generic block element is a block element"
                "that is unknown to DHParser."
            )
        )
        (paragraph
            (text
                "Unknown begin-end-structures are always"
                "considered as block elements and not"
                "as inline elements."
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

Match-test "2"
--------------

### Test-code:
    \begin{generic}
    a single block paragraph
    \end{generic} % ending with
    % a comment
    

### AST
    (generic_block
        (begin_environment
            "generic"
        )
        (paragraph
            (text
                "a single block paragraph"
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

Match-test "3"
--------------

### Test-code:
    \begin{quote}
    a known block element
    \end{quote}

### AST
    (quotation
        (paragraph
            (text
                "a known block element"
            )
            (:Whitespace
                ""
                ""
            )
        )
    )

Fail-test "10"
--------------

### Test-code:
    \begin{generic}inline environment\end{generic}
    

### Messages:
Error: Parser did not match! Invalid source file?
    Most advanced: None
    Last match:    None;
Error: Capture-retrieve-stack not empty after end of parsing: defaultdict(<function Grammar._reset__.<locals>.<lambda> at 0x7f2f0767de18>, {'NAME': ['generic']})

Fail-test "11"
--------------

### Test-code:
    \begin{generic}inline environment
    \end{generic}
    

### Messages:
Error: Parser did not match! Invalid source file?
    Most advanced: None
    Last match:    None;
Error: Parser did not match! Invalid source file?
    Most advanced: None
    Last match:    None;
Error: Capture-retrieve-stack not empty after end of parsing: defaultdict(<function Grammar._reset__.<locals>.<lambda> at 0x7f2f0767dd90>, {'NAME': ['generic']})

Fail-test "12"
--------------

### Test-code:
    \begin{generic}
    invalid enivronment \end{generic}
    

### Messages:
Error: -&LB end_environment LFF expected; "\end{gener" found!
Error: Capture-retrieve-stack not empty after end of parsing: defaultdict(<function Grammar._reset__.<locals>.<lambda> at 0x7f2f0767de18>, {'NAME': ['generic']})


Test of parser: "inline_environment"
====================================


Match-test "1"
--------------

### Test-code:
    \begin{generic}inline environment\end{generic}

### AST
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

Match-test "2"
--------------

### Test-code:
    \begin{generic}inline environment
    \end{generic}

### AST
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

Match-test "3"
--------------

### Test-code:
    $ inline math $

### AST
    (inline_math
        " inline math "
    )

Fail-test "10"
--------------

### Test-code:
    \begin{generic}
    invalid enivronment \end{generic}
    

### Messages:
Error: Parser did not match! Invalid source file?
    Most advanced: None
    Last match:    None;
Error: Parser did not match! Invalid source file?
    Most advanced: None
    Last match:    None;
Error: Capture-retrieve-stack not empty after end of parsing: defaultdict(<function Grammar._reset__.<locals>.<lambda> at 0x7f2f0767de18>, {'NAME': ['generic']})


Test of parser: "itemize"
=========================


Match-test "1"
--------------

### Test-code:
    \begin{itemize}
    \item Items doe not need to be
    \item separated by empty lines.
    \end{itemize}

### AST
    (itemize)

Match-test "2"
--------------

### Test-code:
    \begin{itemize}
    
        \item But items may be
    
        \item separated by blank lines.
    
        \item
    
        Empty lines at the beginning of an item will be ignored.
    
        \end{itemize}

### AST
    (itemize
        (item
            (paragraph
                (text
                    "separated by blank lines."
                )
            )
        )
    )

Match-test "3"
--------------

### Test-code:
    \begin{itemize}
        \item Items can consist of
    
              several paragraphs.
        \item Or of one paragraph
        \end{itemize}

### AST
    (itemize)

Match-test "4"
--------------

### Test-code:
    \begin{itemize}
    \item
      \begin{itemize}
        \item Item-lists can be nested!
      \end{itemize}
    \end{itemize}

### AST
    (itemize
        (item
            (itemize
                (item
                    (paragraph
                        (text
                            "Item-lists can be nested!"
                        )
                        (:Whitespace
                            ""
                            ""
                        )
                    )
                )
            )
        )
    )

Match-test "5"
--------------

### Test-code:
    \begin{itemize}
    \item Item-lists may consist of just one item.
    \end{itemize}

### AST
    (itemize
        (item
            (paragraph
                (text
                    "Item-lists may consist of just one item."
                )
                (:Whitespace
                    ""
                    ""
                )
            )
        )
    )

Fail-test "11"
--------------

### Test-code:
    \begin{itemize}
    Free text is not allowed within an itemized environment!
    \end{itemize}

### Messages:
Error: "\end{itemize}" expected; "Free text " found!
Error: Parser stopped before end! trying to recover...
Error: Parser did not match! Invalid source file?
    Most advanced: None
    Last match:    None;


Test of parser: "enumerate"
===========================


Match-test "1"
--------------

### Test-code:
    \begin{enumerate}
    \item Enumerations work just like item-lists.
    \item Only that the bullets are numbers.
    \end{enumerate}

### AST
    (enumerate)

Match-test "2"
--------------

### Test-code:
    \begin{enumerate}
    \item \begin{itemize}
          \item Item-lists and
          \item Enumeration-lists
             \begin{enumerate}
                \item can be nested
                \item arbitrarily
             \end{enumerate}
          \item Another item
          \end{itemize}
    \item Plain numerated item.
    \end{enumerate}

### AST
    (enumerate)

Match-test "3"
--------------

### Test-code:
    \begin{enumerate} % comment
    
    
        % more comments and paragraph separators
        % yet some more
    
    
        \item %another comment
              finally, the first item
    
    
        % comment
    
    
        \end{enumerate}

### AST
    (enumerate
        (item
            (paragraph
                (text
                    "finally, the first item"
                )
            )
        )
    )

Match-test "4"
--------------

### Test-code:
    \begin{enumerate}
        \item An item
    
              \begin{itemize}
              \item with an enumeration
              \end{itemize}
             as a separate paragraph
        \end{enumerate}

### AST
    (enumerate
        (item
            (paragraph
                (text
                    "An item"
                )
            )
            (itemize
                (item
                    (paragraph
                        (text
                            "with an enumeration"
                        )
                        (:Whitespace
                            ""
                            ""
                        )
                    )
                )
            )
            (paragraph
                (text
                    "as a separate paragraph"
                )
                (:Whitespace
                    ""
                    ""
                )
            )
        )
    )