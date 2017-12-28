

Test of parser: "SubParagraph"
==============================


Match-test "1"
--------------

### Test-code:
    \subparagraph{A subparagraph} with some text
    
    and consisting of several
    
    real paragraphs

### AST
    (SubParagraph
        (heading
            (:Whitespace
                " "
            )
            (text
                "A subparagraph"
            )
            (:Whitespace
                " "
            )
        )
        (paragraph
            (text
                "with some text"
            )
            (:Whitespace
                " "
            )
        )
        (paragraph
            (text
                "and consisting of several"
            )
            (:Whitespace
                " "
            )
        )
        (paragraph
            (text
                "real paragraphs"
            )
            (:Whitespace
                " "
            )
        )
    )


Test of parser: "Paragraph"
===========================


Match-test "1"
--------------

### Test-code:
    \paragraph{A paragraph consisting of several subparagraphs}
    
    Some text ahead
    
    \subparagraph{subparagraph 1}
    
    First subparagraph
    
    \subparagraph{subparagraph 2}
    
    Second subparagraph

### AST
    (Paragraph
        (heading
            (:Whitespace
                " "
            )
            (text
                "A paragraph consisting of several subparagraphs"
            )
            (:Whitespace
                " "
            )
        )
        (paragraph
            (text
                "Some text ahead"
            )
            (:Whitespace
                " "
            )
        )
        (SubParagraph
            (heading
                (:Whitespace
                    " "
                )
                (text
                    "subparagraph 1"
                )
                (:Whitespace
                    " "
                )
            )
            (paragraph
                (text
                    "First subparagraph"
                )
                (:Whitespace
                    " "
                )
            )
        )
        (SubParagraph
            (heading
                (:Whitespace
                    " "
                )
                (text
                    "subparagraph 2"
                )
                (:Whitespace
                    " "
                )
            )
            (paragraph
                (text
                    "Second subparagraph"
                )
                (:Whitespace
                    " "
                )
            )
        )
    )


Test of parser: "Chapters"
==========================


Match-test "1"
--------------

### Test-code:
    \chapter{Chapter 1}
    \section{Section 1}
    \section{Section 2}
    
    Section 2 contains some text
    
    \section{Section 3}
    \subsection{SubSection 1}
    Text for subsection 1
    \subsection{SubSection 2}
    Text for subsection 2
    
    \subsubsection{A subsubsection}
    Text for subsubsecion
    
    \section{Section 4}
    
    \chapter{Chapter 2}
    
    Some text for chapter 2

### AST
    (Chapters
        (Chapter
            (heading
                (:Whitespace
                    " "
                )
                (text
                    "Chapter 1"
                )
                (:Whitespace
                    " "
                )
            )
            (Section
                (heading
                    (:Whitespace
                        " "
                    )
                    (text
                        "Section 1"
                    )
                    (:Whitespace
                        " "
                    )
                )
            )
            (Section
                (heading
                    (:Whitespace
                        " "
                    )
                    (text
                        "Section 2"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (paragraph
                    (text
                        "Section 2 contains some text"
                    )
                    (:Whitespace
                        " "
                    )
                )
            )
            (Section
                (heading
                    (:Whitespace
                        " "
                    )
                    (text
                        "Section 3"
                    )
                    (:Whitespace
                        " "
                    )
                )
                (SubSection
                    (heading
                        (:Whitespace
                            " "
                        )
                        (text
                            "SubSection 1"
                        )
                        (:Whitespace
                            " "
                        )
                    )
                    (paragraph
                        (text
                            "Text for subsection 1"
                        )
                        (:Whitespace
                            ""
                            ""
                        )
                    )
                )
                (SubSection
                    (heading
                        (:Whitespace
                            " "
                        )
                        (text
                            "SubSection 2"
                        )
                        (:Whitespace
                            " "
                        )
                    )
                    (paragraph
                        (text
                            "Text for subsection 2"
                        )
                        (:Whitespace
                            " "
                        )
                    )
                    (SubSubSection
                        (heading
                            (:Whitespace
                                " "
                            )
                            (text
                                "A subsubsection"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                        (paragraph
                            (text
                                "Text for subsubsecion"
                            )
                            (:Whitespace
                                " "
                            )
                        )
                    )
                )
            )
            (Section
                (heading
                    (:Whitespace
                        " "
                    )
                    (text
                        "Section 4"
                    )
                    (:Whitespace
                        " "
                    )
                )
            )
        )
        (Chapter
            (heading
                (:Whitespace
                    " "
                )
                (text
                    "Chapter 2"
                )
                (:Whitespace
                    " "
                )
            )
            (paragraph
                (text
                    "Some text for chapter 2"
                )
                (:Whitespace
                    " "
                )
            )
        )
    )