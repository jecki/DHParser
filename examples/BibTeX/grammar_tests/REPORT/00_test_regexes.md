

Test of parser: "CONTENT_STRING"
================================


Match-test "M1"
---------------

### Test-code:
    https://en.wikipedia.org/w/index.php?title=Duhem\%E2\%80\%93Quine\_thesis\&oldid=77283499122

### AST
    CONTENT_STRING
      :RegExp
        "https://en.wikipedia.org/w/index.php?title=Duhem\"
      ESC
        "%"
      :RegExp
        "E2\"
      ESC
        "%"
      :RegExp
        "80\"
      ESC
        "%"
      :RegExp
        "93Quine\"
      ESC
        "_"
      :RegExp
        "thesis\"
      ESC
        "&"
      :RegExp
        "oldid=77283499122"

Fail-test "F1"
--------------

### Test-code:
    % comment

### Messages:
Error (1040): Parser stopped before end! trying to recover but stopping history recording at this point.