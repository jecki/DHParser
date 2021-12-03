# XML

This example demonstrates how to build an XML-parser on the
basis of an existing grammar. The grammar-definition has
been extracted from: <https://www.w3.org/TR/REC-xml/>

One important lesson this example teaches is that the concrete
syntax tree (as obtained by an auto-generated parser) of a 
DSL-document is not the same as the data-structure encoded by
this document. The latter can be obtained from the former, 
however, by further transformations of the syntax tree.







