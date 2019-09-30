

Test of parser: "content"
=========================


Match-test "simple"
-------------------

### Test-code:
    {Edward N. Zalta}

### AST
    content
      :Token
        "{"
      text
        CONTENT_STRING
          :RegExp
            "Edward"
          WS
            " "
          :RegExp
            "N."
          WS
            " "
          :RegExp
            "Zalta"
      :Token
        "}"

Match-test "nested_braces"
--------------------------

### Test-code:
    {\url{https://plato.stanford.edu/archives/fall2013/entries/thomas-kuhn/}}

### AST
    content
      :Token
        "{"
      text
        CONTENT_STRING
          "\url"
        :Token
          "{"
        text
          CONTENT_STRING
            "https://plato.stanford.edu/archives/fall2013/entries/thomas-kuhn/"
        :Token
          "}"
      :Token
        "}"


Test of parser: "entry"
=======================


Match-test "entry"
------------------

### Test-code:
    @Online{wikipedia-duhem-quine,  % A
      editor       = {Wikipedia},
      title        = {Duhem-Quine thesis},  % B
      year         = {2017},
      date         = {2017-08-19 % C
       },
      url          = {https://en.wikipedia.org/w/index.php?title=Duhem\%E2\%80\%93Quine\_thesis\&oldid=772834991},
      organization = {Wikipedia}
    }

### AST
    entry
      :RegExp "@"
      type
        WORD "Online"
      :Token "{"
      key
        NO_BLANK_STRING "wikipedia-duhem-quine"
      :Token ","
      :Whitespace
        "  % A"
        "  "
      field
        WORD
          :RegExp "editor"
          :Whitespace "       "
      :Token "="
      :Whitespace " "
      content
        :Token "{"
        text
          CONTENT_STRING "Wikipedia"
        :Token "}"
      :Token ","
      :Whitespace
        ""
        "  "
      field
        WORD
          :RegExp "title"
          :Whitespace "        "
      :Token "="
      :Whitespace " "
      content
        :Token "{"
        text
          CONTENT_STRING
            :RegExp "Duhem-Quine"
            WS " "
            :RegExp "thesis"
        :Token "}"
      :Token ","
      :Whitespace
        "  % B"
        "  "
      field
        WORD
          :RegExp "year"
          :Whitespace "         "
      :Token "="
      :Whitespace " "
      content
        :Token "{"
        text
          CONTENT_STRING "2017"
        :Token "}"
      :Token ","
      :Whitespace
        ""
        "  "
      field
        WORD
          :RegExp "date"
          :Whitespace "         "
      :Token "="
      :Whitespace " "
      content
        :Token "{"
        text
          CONTENT_STRING
            :RegExp "2017-08-19"
            WS
              " % C"
              "   "
        :Token "}"
      :Token ","
      :Whitespace
        ""
        "  "
      field
        WORD
          :RegExp "url"
          :Whitespace "          "
      :Token "="
      :Whitespace " "
      content
        :Token "{"
        text
          CONTENT_STRING
            :RegExp "https://en.wikipedia.org/w/index.php?title=Duhem\"
            ESC "%"
            :RegExp "E2\"
            ESC "%"
            :RegExp "80\"
            ESC "%"
            :RegExp "93Quine\"
            ESC "_"
            :RegExp "thesis\"
            ESC "&"
            :RegExp "oldid=772834991"
        :Token "}"
      :Token ","
      :Whitespace
        ""
        "  "
      field
        WORD
          :RegExp "organization"
          :Whitespace " "
      :Token "="
      :Whitespace " "
      content
        :Token "{"
        text
          CONTENT_STRING "Wikipedia"
        :Token "}"
        :Whitespace
          ""
          ""
      :Token "}"