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
"compilation-methods". It is also possible, though less common, to add
"attr_ATTRIBUTENAME"-methods that will be called on all those nodes that have an
attribute of that name. The Compiler-class itself is callable and the
compilation-process is initiated by calling an instance of this class (or a
class derived from "Compile") with the (AST-)tree as argument.

For nodes for which no "on_NAME"-method has been defined, class compile simply
calls the compilation-methods for all children (if any) and updates the node's
result-tuple with the return values of the children's compilation-call that are
not None. This :py:meth:`~compile.Compiler.fallback_compiler`-method silently
assumes that the compilation methods do return a (transformed)- node. Since the
fallback-method fails in any case where the result of a child's compilation is
not a Node, the fallback-method must be overridden for compilers that yield
other data-structures than node-trees. Or it must be made sure otherwise that
the "fallback_compiler"-method will never be called, for example by providing
"on_NAME"-methods for all possible node-names. This technique has been used in
the JSON-compiler-example in the "Overview"-section of this manual (see
`json_compiler`_). 

Using class :py:class:`~compile.Compiler` for merely transforming data or using
it for deriving different kinds data-structures or even, as with a classical
compiler, a runnable piece of code, are different use cases that require
slightly different design patterns. We will look at each of these use cases
separately in the following.

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

Where we would like to get to, is the data-tree that when serialized looks
more or less like the original XML::

    <line>Herz, mein Herz ist traurig</line>  

In order to extract the tree-data that has been encoded in the XML-source, we
need a compiler that can compile XML-syntax-trees to XML-data-trees. (We can
skip the AST-transformation-step, because with the @drop-directive in the
grammar, the concrete syntax tree has already sufficiently been streamlined for
further processing). In order to do so, we need to write compilation-methods at
least for the node-types "document", "element" and "content". We do not really
need compilation-methods for "STag" and "ETag", because these will be dropped,
anyway. Similarly, "CharData" does not need to be compiled, because it is a
leaf-node the content of which shall not be changed, anyway. And the elimination
of "CharData"-nodes happens on the level below "CharData". (Of course, this is
just one way of writing a syntax-tree to data-tree converter, other approaches
with different decisions on which compilation-methods are implemented are also
imaginable.)

The compilation-methods typically follow one or the other of the following two 
patterns:

.. code-block:: python

    # Tree-transformation-pattern
    def on_NAME(self, node: Node) -> Node:
        node = self.fallback_compiler(node)
        ...
        return node

    # Generalized-compilation-pattern
    def on_NAME(self, node: Node) -> Any:
        node.result = tuple(self.compile(child) for child in self.children)
        ...
        return node   # could also be anything other than a node-object

"NAME" does here stand as placeholder for any concrete node-name.

The first pattern works only for compilers that yield tree-structures, because,
as said, :py:meth:`~compile.Compiler.fallback_compiler` assumes that the
returned result of any compilation function is a node.
:py:meth:`~compile.Compiler.compile` does not make this assumption. Therefore,
the second pattern can be employed in either use-case. In any case, calling
compilation-methods of child-nodes should always be channeled through one of the
two methods "fallback_compiler()" or "compile()", because these methods make
sure the "self.trail"- variable (which keeps the "trail" of nodes from the
root-node to the current node) will be updated and that any
"attr_NAME()"-methods are called, plus a few other things. 

It is not necessary to call the compilation-methods of the child-nodes right at
the beginning of the compilation-method as these patterns suggest, or to call
them at all. Rather, the compilation-method decides when and for which children
the compilation-methods will be called. 

With this in mind the following code that compiles the XML-syntax-tree into 
the XML-data-tree should be easy to understand::

    >>> from DHParser.nodetree import Node
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
    ...         node.name = node[0].name
    ...         node.result = node[0].result
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

Like all tree-transformations in DHParser, Compilation-methods are free to
change the tree in-place. If you want to retain the structure of the tree before
compilation, the only way to do so is to make a deep copy of the node-tree,
before calling the Compiler-object. Still, compilation-methods must always
return the result of the compilation! In cases where the return value of
a compilation-method is a Node-object, it is not necessary (i.e. nowhere
silently assumed) that the returned node-object is the same as the node-object
that has been passed as a parameter. It can be an entirely freshly constructed
Node-object. 

Observe the use of a reset()-method: This method is called by the
__call__-method of :py:class:`~compile.Compiler` before the compilation starts
and should be used to reset any object-variables which may still contain values
from the last compilation-run to their default values. 

Let's see, how our XMLTransformer-object produces the actual data tree::

    >>> syntaxtree_to_datatree = XMLTransformer()
    >>> data = syntaxtree_to_datatree(data)
    >>> print(data.as_xml())
    <line>Herz, mein Herz ist traurig</line>


Compiling to other structures
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In order to illustrate how compiling a syntax-tree to a data-structure that
is not a node-tree, any more, we use a simplified (and somewhat sloppy)
JSON-parser as an example. Here is the simplified JSON-Grammar::

    >>> json_grammar = '''
    @literalws  = right  # eat insignificant whitespace to the right of literals
    @whitespace = /\s*/  # regular expression for insignificant whitespace
    @drop       = whitespace, strings  # silently drop bare strings and whitespace
    @disposable = /_\w+/  # regular expression to identify disposable symbols

    json        = ~ _element _EOF
    _element    = object | array | string | other_literal
    object      = "{" member { "," §member } §"}"
    member      = string §":" _element
    array       = "[" [ _element { "," _element } ] §"]"
    string      = `"` §/[^"]+/ `"` ~
    other_literal = /[\w\d.+-]+/~
    _EOF        =  !/./
    '''

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



