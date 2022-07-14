Compiling
=========

Module ``compile`` provides the scaffolding for further tree-processing stages
after the AST-transformation as well as for the compilation of syntax or
document-trees to different kinds of data.

The most simple case is the one where there is only one further processing-stage
after AST-Transformation and this last stage is called "compilation" no matter
whether its outcome is another and now final tree-structure representing the
processed source document or a different kind of data structure. For this
purpose module ``compile`` provides the class :py:class:`~compile.Compiler` as
scaffolding. 

Just as with the transformation-table for the AST-transformation, using the
Compile-class is a suggestion, not a must. You are free to implementation your
very own transformation function(s) from scratch or - as long as only tree to
tree-transformations are concerned - the table-based transformation provided by
:py:mod:`~transform` that is recommended for the CST-to-AST-transformation-step. 

Also, you are free to add as many transformation steps in-between the AST and
the end-result as you like. It is even not untypical for digital humanities
projects to have bifurcations in the processing pipeline, where one bifurcations
leads to say, the pdf-generation for a printable document and another
bifurcation yields an HTML-output to be viewed online.

All of this is to a stronger or lesser degree supported by DHParser under the
condition that all intermediary transformations in any bifurcation still yield
trees. Only the very last transformation may yield a different data type. Or,
put it differently, the processing-pipeline support of DHParser ends after the
first transformation that does not yield a node-tree any more.

Class Compiler
--------------

Class :py:class:`~compile.Compiler` provides the scaffolding for
tree-transformations based on the visitor-pattern. Typically, you'd derive a
custom-compilation class from the "Compiler"-class and add "on_NAME"-methods for
transforming nodes with a particular name. These methods are calle the
"compilation-methods". (You can also add "attr_ATTRIBUTENAME"-methods that will
be called on all those nodes that have an attribute of that name.) The
Compiler-class itself is callable and the compilation-process is initiated by
calling an instance of this class (or a class derived from "Compile") with the
(AST-)tree as argument.

For nodes for which no "on_NAME"-method has been defined, class compile simply
calls the compilation-methods for all children (if any) and updates the node's
result-tuple with the return values of the children's compilation-call that are
not None. This :py:meth:`~compile.Compiler.fallback_compiler`-method silently
assumes that the compilation methods do return a (transformed)- node. Since the
fallback-method fails in any case where the result of a child's compilation is
not a Node, the fallback-method must be overridden in sub-classes that yield
other data-structures than node-trees. Or it must be made sure otherwise that
the "fallback_compiler"-method will never be called, for example by providing
"on_NAME"-methods for all possible node-names. This technique has been used in
the JSON-compiler-example in the "Overview"-section of this manual (see
`json_compiler`_). 

Using class :py:class:`~compile.Compiler` for merely transforming data on the one
hand side or using it for deriving different kinds data-structures or even, as 
with a classical compiler, a runnable piece of code on the other hand side, are
different use cases that require slightly different design patterns. We will look 
at each of these use cases separately in the following.

Transforming node-trees
^^^^^^^^^^^^^^^^^^^^^^^

Let's first see how class :py:class:`~compile.Compiler` can be used to transform
node-trees. As an example we use a rudimentary XML-parser that only parses tags
and text but no empty elements, attributes, comments, processing instructions,
declarations and the like::

    >>> mini_xml_grammar = """
    ...     @ whitespace  = /\s*/
    ...     @ disposable  = EOF
    ...     @ drop        = EOF, whitespace, strings
    ...
    ...     document = ~ element ~ §EOF
    ...
    ...     element  = STag §content ETag
    ...     STag     = '<' TagName §'>'
    ...     ETag     = '</' TagName §'>'
    ...     TagName  = /\w+/
    ...     content  = [CharData] { element [CharData] }
    ...
    ...     CharData = /(?:(?!\]\]>)[^<&])+/
    ...     EOF      =  !/./ 
    ... """
    >>> from DHParser.dsl import create_parser 
    >>> xml_parser = create_parser(mini_xml_grammar)

Now, without any further processing, a pure XML-parser does not yield the tree-data
encoded in an XML-source, but the syntax tree of that XML-encoded text:: 

    >>> xml_source = "<line>Herz, mein Herz ist traurig</line>"
    >>> data = xml_parser(xml_source)
    >>> print(data.as_xml())
    <document>
      <element>
        <STag>
          <TagName>line</TagName>
        </STag>
        <content>
          <CharData>Herz, mein Herz ist traurig</CharData>
        </content>
        <ETag>
          <TagName>line</TagName>
        </ETag>
      </element>
    </document>

In order to extract the tree-data that has been encoded in the XML-source, we 
need a compiler that can compile XML-syntax-trees to XML-data-trees. (We can 
skip the AST-transformation-step, because with the @drop-directive in the
grammar, the concrete syntax tree has already sufficiently been streamlined for
further processing)::

    >>> from DHParser.compile import Compiler
    >>> class XMLTransformer(Compiler):
    ...     def reset(self):
    ...         super().reset()
    ...         # don't keep pure whitespace nodes in mixed content
    ...         self.preserve_whitespace = False
    ...
    ...     def on_document(self, node: Node) -> Node:
    ...         # compile all descendants
    ...         node = self.fallback_compiler(node)
    ...         # then reduce document node to its single element
    ...         assert len(node.children) == 1
    ...         node.result = node[0].result
    ...         node.name = 'element'
    ...         return node
    ...
    ...     def on_content(self, node: Node) -> Node:
    ...         node = self.fallback_compiler(node)
    ...         if len(node.children) == 1:
    ...             if node[0].name == 'CharData':
    ...                  # eliminate solitary CharData-nodes
    ...                 node.result = node[0].result
    ...         else:
    ...             # remove CharData nodes that contain only whitespace
    ...             node.result = tuple(child for child in node.children
    ...                                 if child.name != 'CharData' \
    ...                                 or self.preserve_whitespace \
    ...                                 or child.content.strip())
    ...         return node
    ...
    ...     def on_element(self, node: Node) -> Node:
    ...         node = self.fallback_compiler(node)
    ...         tag_name = node['STag']['TagName'].content
    ...         if node['ETag']['TagName'].content != tag_name:
    ...             self.tree.new_error(
    ...                 node['ETag'], "Mismatch of opening and closing tag!")
    ...         # set element-name to tag-name
    ...         node.name = tag_name
    ...         # drop opening and closing tag and reduce content-node
    ...         node.result = node['content'].result
    ...         return node

Other than with the table-based-transformation that is used in :py:mod:`~transform`
each the compilation/transformation-methods of classes derived from :py:class:`~compile.Compiler`
are themselves responsible for calling the compiler-functions for their child-nodes. Also,
even though it is assumed that compilation, just like any other tree-transformation, may
change the tree in-place, every compilation-method (i.e. "on_XXX()") must return the result
of the the compilation. In this case where the compilation-methods merely transform the
tree, the result is also a node. It is not necessary (i.e. nowhere silently assumed) that
the node object passed as a parameter is the same as the result-node that is returned.



    >>> syntaxtree_to_datatree = XMLTransformer()


Compiling to other structures
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is an excerpt from that Compiler-class, again:

.. code-block:: python

  JSONType = Union[Dict, List, str, int, float, None]

    class jsonCompiler(Compiler):
        def __init__(self):
            super(jsonCompiler, self).__init__()
            self._None_check = False  # set to False if any compilation-method is allowed to return None


        def reset(self):
            super().reset()
            # initialize your variables here, not in the constructor!

        def on_json(self, node) -> JSONType:
            assert len(node.children) == 1
            return self.compile(node[0])

        def on_object(self, node) -> Dict[str, JSONType]:
            return { k: v for k, v in (self.compile(child) for child in node)}

        def on_member(self, node) -> Tuple[str, JSONType]:
            assert len(node.children) == 2
            return (self.compile(node[0]), self.compile(node[1]))
        
        ...


A few specifics about compilation-functions are noteworthy, here::

1. The use of a reset()-method: This method is called by the __call__-method of 
   :py:class:`~compile.Compiler` before the compilation starts and should be
   used to reset any object-variables, which may still contain values from the
   last compilation-run to their default values. 

   There are two further methods that can be overridden an will be called during 
   each call of a Compiler-object, namely :py:meth:`~compile.Compiler.prepare`
   and :py:meth:`~compile.Compiler.finalize`. These allow a fine-grained control
   of initialization an de-initialization of any variables or other resources
   needed during compilation. It is furthermore possible to add any function
   you'd like to the finalizers-list of the Compiler-object at any time during
   compilation. This allows to defer certain tasks to the end of the 
   compilation-process.

2. Compilation-methods receive a node object as argument and are required to
   return the result of the compilation of this node object. The Compiler-object
   assumes that if any compilation function returns ``None`` then the return
   statement has been forgotten and raises and Error. In cases where ``None``
   is a reasonable compilation result (as with our JSON-compiler), this check can
   be turned of by setting the ``_None_check``-flag of to ``False`` in the 
   constructor.

3. Compilation-methods can get access to the "trail" (i.e. the list of nodes
   leading up from the root of the tree to the node that has been passed to the
   compilation-method as argument) via ``self.trail``. (This does not happen
   in the example above, though.)

4. Compilation-methods route calling the compilation-methods of any 
   child-objects through the :py:meth:`~compile.Compiler.compile`-method
   of the :py:class:`~compile.Compiler`-object or - in case of pure
   tree-transformations through :py:meth:`~compile.fallback_compiler`.

   These methods take care of picking the right compilation method, 
   updating the "trail"-field as well as a few other things. It is not
   advisable to call one compilation-method from another compilation-method
   directly.



