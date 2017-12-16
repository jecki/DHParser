

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
            "A subparagraph"
        )
        (paragraph
            (text
                "with some text"
            )
        )
        (paragraph
            (text
                "and consisting of several"
            )
        )
        (paragraph
            (text
                "real paragraphs"
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
            "A paragraph consisting of several subparagraphs"
        )
        (paragraph
            (text
                "Some text ahead"
            )
        )
        (SubParagraph
            (heading
                "subparagraph 1"
            )
            (paragraph
                (text
                    "First subparagraph"
                )
            )
        )
        (SubParagraph
            (heading
                "subparagraph 2"
            )
            (paragraph
                (text
                    "Second subparagraph"
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
                "Chapter 1"
            )
            (Section
                (heading
                    "Section 1"
                )
            )
            (Section
                (heading
                    "Section 2"
                )
                (paragraph
                    (text
                        "Section 2 contains some text"
                    )
                )
            )
            (Section
                (heading
                    "Section 3"
                )
                (SubSection
                    (heading
                        "SubSection 1"
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
                        "SubSection 2"
                    )
                    (paragraph
                        (text
                            "Text for subsection 2"
                        )
                    )
                    (SubSubSection
                        (heading
                            "A subsubsection"
                        )
                        (paragraph
                            (text
                                "Text for subsubsecion"
                            )
                        )
                    )
                )
            )
            (Section
                (heading
                    "Section 4"
                )
            )
        )
        (Chapter
            (heading
                "Chapter 2"
            )
            (paragraph
                (text
                    "Some text for chapter 2"
                )
            )
        )
    )