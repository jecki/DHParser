

Test of parser: "content"
=========================


Match-test "simple"
-------------------

### Test-code:
    {Edward N. Zalta}

### AST
    <content>
      <:Token>{</:Token>
      <text>
        <CONTENT_STRING>Edward N. Zalta</CONTENT_STRING>
      </text>
      <:Token>}</:Token>
    </content>

Match-test "nested_braces"
--------------------------

### Test-code:
    {\url{https://plato.stanford.edu/archives/fall2013/entries/thomas-kuhn/}}

### AST
    <content>
      <:Token>{</:Token>
      <text>
        <CONTENT_STRING>\url</CONTENT_STRING>
        <:Series>
          <:Token>{</:Token>
          <text>
            <CONTENT_STRING>https://plato.stanford.edu/archives/fall2013/entries/thomas-kuhn/</CONTENT_STRING>
          </text>
          <:Token>}</:Token>
        </:Series>
      </text>
      <:Token>}</:Token>
    </content>