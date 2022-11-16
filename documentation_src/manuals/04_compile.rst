Compiling
=========

Module :py:mod:`compile` provides the scaffolding for further tree-processing stages
after the AST-transformation as well as for the compilation of syntax or
document-trees to different kinds of data.

The most simple case is the one where there is only one further processing-stage
after AST-Transformation and this last stage is called "compilation" no matter
whether its outcome is another and now final tree-structure representing the
processed source document or a different kind of data structure. For this
purpose module :py:mod:`compile` provides the class :py:class:`~compile.Compiler` as
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
custom-compilation class from the "Compiler"-class and add "on_NAME"-methods
(or "node-handlers") for
transforming nodes with a particular name. These methods are called the
"compilation-methods". It is also possible, though less common, to add
"attr_ATTRIBUTENAME"-methods that will be called on all those nodes that have an
attribute of that name. The Compiler-class itself is callable and the
compilation-process is initiated by calling an instance of this class (or a
class derived from "Compile") with the (AST-)tree as argument.

For nodes for which no "on_NAME"-method has been defined, class compile simply
calls the compilation-methods for all children (if any) and updates the node's
result-tuple with the return values of the children's compilation-call that are
not None. This :py:meth:`~compile.Compiler.fallback_compiler`-method silently
assumes that the compilation methods do return a (transformed) node. Since the
fallback-method fails in any case where the result of a child's compilation is
not a Node, the fallback-method must be overridden for compilers that yield
other data-structures than node-trees. Or it must be made sure otherwise that
the "fallback_compiler"-method will never be called, for example by providing
"on_NAME"-methods for all possible node-names. This technique has been used in
the JSON-compiler-example in the "Overview"-section of this manual (see
:ref:`json_compiler`). 

Using class :py:class:`~compile.Compiler` for merely transforming data or using
it for deriving different kinds data-structures or even, as with a classical
compiler, a runnable piece of code, are different use cases that require
slightly different design patterns. We will look at each of these use cases
separately in the following.

Transforming
^^^^^^^^^^^^

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
sure the "self.path"- variable (which keeps the "path" of nodes from the
root-node to the current node) will be updated and that any
"attr_NAME()"-methods are called.

The "fallback_compiler"-method furthermore ensures that changes in the
composition of ancestor-nodes a) do not mess up the tree traversal and b) do
not overwrite node-objects returned by the node-handlers. The algorithm of
"fallback_compiler" runs through the tuple of children in the state at
the time the call is issued. If during this pass the tuple of children is
exchanged by a modified tuple of children, for example because a child is
dropped from the tree, this will not affect the tuple of children that
"fallback_compiler" iterates over. So all children's handlers will be
called even if a child is dropped and the result of its handler will
subsequently be ignored. By the same token, handlers of children added
during the pass will not be called. Once, the pass is finished, the children
still present in the tuple (and only those!) will be replaced by the result
of their handler. This may sound complicated, but it is - as I believe -
more or less the behavior that you would intuitively expect.

However that may be, in order to keep
the compiler-structure clean and comprehensible, it is generally advisable
manipulate only the child-composition of the node or its descendants in a
handler but not that of its parent or farther ancestor(s). Still, as rules are there to be
broken, it can sometimes become necessary to ignore this advice. The algorithm
that "fallback_compiler" employ for tree-traversal allow you to ignore it
safely. It is still dangerous and, therefore, expressly not recommended to
manipulate the sibling-composition!

It is not necessary to call the handlers of the child-nodes right at
the beginning of the handler as these patterns suggest, or to call
them at all. Rather, the compilation-method decides if and when and, possibly,
also for which children the compilation-methods will be called. Other,
than the traversal implemented in :py:mod:`~transfom`, which is always
depth-first, the order of the traversal can be determined freely and may
even vary for different sub-trees.

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


As can be seen, it is not necessary to fill in a compilation method for each
and every node-type that can appear in the syntax-tree. When the Compiler-object
is used for tree-transformation, it suffices to fill in compilation-methods
only where necessary.

Most of the magic is contained in the "on_element"-method, which renames the
"element"-nodes with the tag-name found in its starting- and ending-tag-children
and then drops these children entirely. (Because they will be dropped anyway,
it is not necessary to define a compilation-method for the STag and ETag-nodes!)
Finally, the remaining "content"-child is reduced to the renamed element-node.

Like all tree-transformations in DHParser, Compilation-methods are free to
change the tree in-place. If you want to retain the structure of the tree before
compilation, the only way to do so is to make a deep copy of the node-tree,
before calling the Compiler-object. Still, compilation-methods must always
return the result of the compilation! In cases where the return value of
a compilation-method is a Node-object, it is not necessary (i.e. nowhere
silently assumed) that the returned node-object is the same as the node-object
that has been passed as a parameter. It can be a newly constructed
Node-object, as well.

Observe the use of a reset()-method: This method is called by the
``__call__``-method of :py:class:`~compile.Compiler` before the compilation starts
and should be used to reset any object-variables which may still contain values
from the last compilation-run to their default values. 

Let's see, how our XMLTransformer-object produces the actual data tree::

    >>> syntaxtree_to_datatree = XMLTransformer()
    >>> data = syntaxtree_to_datatree(data)
    >>> print(data.as_xml())
    <line>Herz, mein Herz ist traurig</line>


Compiling to other structures
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here is an excerpt from that Compiler-class, again:

    >>> json_grammar = '''
    ... @literalws  = right  # eat insignificant whitespace to the right of literals
    ... @whitespace = /\s*/  # regular expression for insignificant whitespace
    ... @drop       = whitespace, strings  # silently drop bare strings and whitespace
    ... @disposable = /_\w+/  # regular expression to identify disposable symbols
    ...
    ... json        = ~ _element _EOF
    ... _element    = object | array | string | other_literal
    ... object      = "{" member { "," §member } §"}"
    ... member      = string §":" _element
    ... array       = "[" [ _element { "," _element } ] §"]"
    ... string      = `"` §/[^"]+/ `"` ~
    ... other_literal = /[\w\d.+-]+/~
    ... _EOF        =  !/./ '''

Let's now test this grammar, with a small piece of JSON::

    >>> json_parser = create_parser(json_grammar)
    >>> st = json_parser('{"pi": 3.1415}')
    >>> print(st.as_sxpr())
    (json
      (object
        (member
          (string
            (:Text '"')
            (:RegExp "pi")
            (:Text '"'))
          (other_literal "3.1415"))))

Despite the early-on simplifications that have been configured by the
"@disposable"- and the "@drop"-directives, the concrete-syntax-tree, is still a
bit verbose. So we, furthermore define an abstract-syntax-tree-transformation::

    >>> from DHParser.transform import traverse, remove_tokens, reduce_single_child
    >>> json_AST_trans = {"string": [remove_tokens('"'), reduce_single_child]}
    >>> st = traverse(st, json_AST_trans)
    >>> print(st.as_sxpr())
    (json (object (member (string "pi") (other_literal "3.1415"))))

Now, let's write a compiler that compiles the abstract-syntax-tree of
a JSON-file into a Python data-structure::

    >>> from typing import Dict, List, Tuple, Union
    >>> JSONType = Union[Dict, List, str, int, float, None]
    ...
    >>> class simplifiedJSONCompiler(Compiler):
    ...     def __init__(self):
    ...         super(simplifiedJSONCompiler, self).__init__()
    ...         self.forbid_returning_None = False  # None will be returned when compiling "null"
    ...
    ...     def on_json(self, node) -> JSONType:
    ...         assert len(node.children) == 1
    ...         return self.compile(node[0])
    ...
    ...     def on_object(self, node) -> Dict[str, JSONType]:
    ...         return {k: v for k, v in (self.compile(child) for child in node)}
    ...
    ...     def on_member(self, node) -> Tuple[str, JSONType]:
    ...         assert len(node.children) == 2
    ...         return (self.compile(node[0]), self.compile(node[1]))
    ...
    ...     def on_array(self, node) -> List[JSONType]:
    ...         return [self.compile(child) for child in node]
    ...
    ...     def on_string(self, node) -> str:
    ...         return node.content
    ...
    ...     def on_other_literal(self, node) -> Union[bool, float, None]:
    ...         content = node.content
    ...         if content == "null":    return None
    ...         elif content == "true":  return True
    ...         elif content == "false": return False
    ...         else:                    return float(content)

The essential characteristics of this pattern (i.e. compilation of a node-tree
to a data-structure that is not a node-tree, any more) are:

1. For each possible, or rather, reachable node-type an "on_NAME"-method has been
   defined. So the fallback that silently assumes that the compilation-result
   is going to be yet another node-tree will never be invoked.
2. Compilation-methods are themselves responsible for compiling the child-nodes
   of "their" node, if needed. They always do so by calling the "compile"-method
   of the superclass on the child-nodes.
3. Every compilation-method returns the complete (compiled) data-structure that
   the tree originating in its node represents.
4. By the same token each compilation method that calls "Compiler.compile" on
   any of its child-nodes is responsible for integrating the results of these
   calls into its own return value.
5. Compilation-methods can and must make assumptions about the structure of the
   subtree that has been passed as the node-argument. (For example,
   "member"-nodes of the JSON-AST always have exactly two children.) These
   assumptions must be warranted by the grammar in combination with the
   AST-transformation. Their validity can be checked with "assert"-statements.
   As of now, DHParser does not offer any support for structural tree-validation.
   (If really needed, though, the tree could be serialized as XML and validated
   with common XML-tools against a DTD, Relax-NG-schema or XML-schema.)

Now, let's see our JSON-compiler in action::

    >>> json_compiler = simplifiedJSONCompiler()
    >>> data = json_compiler(st)
    >>> print(data)
    {'pi': 3.1415}

A slightly more complex example will follow further below.

Initializing and Finalizing
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Class compiler provides several hooks to initialize or
prepare the compilation-process before it is started and to finalize
it after it has been finished. For initialization, there are two
methods that can be overloaded:

1. the :py:meth:`~compile.Compiler.reset`-method which is called both by the
   constructor (i.e. "__init__"-method) of the class and at the very beginning
   of the :py:meth:`~compile.Compiler.__call__`-method. It's purpose is to
   initialize or reset all variables that need to be reset anew every time
   the compiler is invoked by running the Compile-object.

   The reset method should contain all initializations that can be done
   independently of the concrete node-tree that is going to be compiled.

2. the :py:meth:`~compile.Compiler.prepare`-method which will be called
   just before the first compile-method, i.e. the compile-method of the
   root-node is called. The prepare-method will receive the root-node of
   the tree to be compiled as argument and can therefore perform any kind
   of initializations that require knowledge about the concrete data that
   is going to be compiled.

For finalization, there are again two "hooks", although of different kind:

1. the :py:meth:`~compile.Compiler.finalize`-method, which will be called after the
   compilation has been finished and which receives the result of the
   compilations (whatever that may be) as parameter and returns the
   (possibly) altered result. The purpose of the finalize method is to
   perform wrap-up-tasks that require access to the complete
   compilation-result, before they can be performed. This is the preferred
   place for coding finalizations.

2. a list of finalizers ("Compiler.finalizers"). This feature is EXPERIMENTAL
   and may be removed in the future! The list is a list of
   pairs (function, parameter-tuple), which will be executed in order
   after the compilation has been finished, but before the
   Compiler.finalize-method is called.

   While it would of course be possible to concentrate all wrap-up task in the
   finalizer-method, the mechanism of the finalizer-list can be convenient,
   because it allows to define a wrap-up tasks as local functions of
   compilation-methods and defer their execution to the end of the overall
   compilation-process. Or, in other words, finalizer-tasks can be defined
   within the context to which they are logically connected. A typical use case
   are structural changes to the data-tree which could hamper the compilation if
   not deferred till the very end.

   A disadvantage of finalizers in contrast to the finalization-method, however,
   is that it becomes harder to keep unexpected side effects of finalizers on
   other finalizers in check if the various finalizers are contextually
   separated from each other.

.. _processing_pipelines:

Processing Pipelines
--------------------

The standard-pipeline
^^^^^^^^^^^^^^^^^^^^^

When compiling a document in a domain specific notation or language, DHParser assumes
the same standard-pipeline of four steps: 

1. *preprocessing*, which is a str -> str transformation. More precisely, it
   takes a text document as input and yields a text document as well as a
   source-mapping-table as output. The output document of the preprocessor is
   usually a modified version of the input document. 

2. *parsing*, which is a str -> node-tree transformation. More precisely, it yields
   the (potentially already somewhat simplified) concrete syntax-tree of the 
   input-text. A list of parsing-errors may have been attached to the root-node of
   that syntax-tree.
   
3. *AST-transformation*, which is a node-tree -> node-tree transformation that 
   converts the concrete syntax-tree (in-place) into the abstract-syntax-tree. Again,
   errors may have been added to the error-list of the root-node.

4. *compiling*: which is a node-tree -> anything transformation. More precisely, it
   takes the abstract-syntax-tree as input and yields the compiled data as output. 
   What format the compiled data is, depends entirely on the compiler. It can be 
   a another node-tree, but also anything else. The abstract-syntax-tree may be 
   changed or even destroyed during the compilation. In any case, errors that occur
   during compilation will again be reported to the root-node of the tree and can
   later be collected by accessing ``root.errors``

The xxxParser.py-script that is autogenerated by DHParser when compiling an
EBNF-grammar provides transformation-functions for each of these steps and
generators that yield a thread-local-version of each of these
transformation-functions or callable transformation-classes.

Module :py:mod:`DHParser.compile` provides the helper function 
:py:func:`DHParser.compile.compile_source` that calls these four stages in
sequence and collects the result, i.e. the output of the last stage, the
error messages, if any, and, optionally, the AST-tree. Example::

   >>> from DHParser.compile import compile_source
   >>> json_str = '{"test": ["This", "is", 1, "JSON", "test"]}'
   >>> json_objs, errors, ast = compile_source(json_str, None,
   ...                              json_parser,
   ...                              lambda tree: traverse(tree, json_AST_trans),
   ...                              simplifiedJSONCompiler(),
   ...                              preserve_AST=True)
   >>> json_objs
   {'test': ['This', 'is', 1.0, 'JSON', 'test']}
   >>> errors
   []
   >>> print(ast.as_sxpr())
   (json
     (object
       (member
         (string "test")
         (array
           (string "This")
           (string "is")
           (other_literal "1")
           (string "JSON")
           (string "test")))))

Subsequent stages of the processing pipeline will only be called if no fatal errors 
have occurred in any of the earlier stages. This means that when designing the
AST-transformation, the compiler and, if the extended pipeline (see below) is used,
any further processing stages, it should be provided for the case that the input
is faulty stemming from earlier stages can to some degree (determined by your assignment
or seriousness to different possible errors) be faulty.

Function :py:func:`DHParser.compile.process_tree` is a convenient helper function
that calls a given processing stage only, if the tree handed over from the last stage
does not contain any fatal errors. Thus, a sequence of processing stages can be
written as a sequence of calls of :py:func:`DHParser.compile.process_tree` without
the need of any if clauses the check the results for fatal errors after each call.

The extended pipeline
^^^^^^^^^^^^^^^^^^^^^

There are many contexts where the four above-mentioned stages are not sufficient. In
the digital humanities, for example, it is typical that the data is passed through 
many different tree-processing stages, before it is transformed into a form that is
not a tree, any more. And it is not at all uncommon that this processing pipeline
is bifurcated as the following schema, taken from the 
`Medieval Latin dictionary <https://mlw.badw.de>`_
or the `Bavarian Academy of Sciences and Humanities <https://www.badw.de>`_, shows::

    ----------------    
    | source (DSL) |
    ---------------- 
           |
           |--- Parsing
           |
        -------
        | CST |
        -------
           |
           |--- AST-Transformation
           |
        -------
        | AST |
        -------
           |
           |--- data-consolidation
           |
      ------------
      | data-XML |
      ------------
           |
           |--- output-transformation
           |    
     -------------- print-transform. ------------- TeX-compilation -----------
     | output-XML |----------------->| print-XML |---------------->| ConTeXt |
     --------------                  -------------                 -----------
           |
           |--- HTML-Transformation
           |
        --------
        | HTML |
        --------

In this particular example, there is no preprocessing stage. The first three
remaining stages are covered by the "standard pipeline" (i.e. parsing,
AST-transformation, compilation). The following stages, starting from data-XML,
form the extended pipeline.

In order to support extended processing pipeline :py:mod:`DHParser.compile` uses
the very simple concept of junctions, where a junctions is the connection of an
earlier stage (origin) in the the pipeline to a following stage (target) via a
transformation or compilation function. Pipelines are created by providing
junctions from for each intermediate stage from the starting stage (usually the
last stage of the standard pipeline) to one or more ending stages. Bifurcations a
created simply by providing to different junctions starting from the same origin
stage. (It is not allowed to have more than one junction for one and the same
target stages.)

The stages are identified by the names which may be chosen arbitrarily as long
as each name is used for one and the same stage, only. Technically, a junction
is a triple of the name of the origin stage, a factory function that returns a
transformation-callable and the name of the target stage. A (potentially
bifurcated) pipeline is then simply a set of junctions that covers all routes
from the starting stage(s) of the pipeline to its ending stage(s).

We will illustrate this by extending our example of simplified json-compiler to a 
processing pipeline. So far the standard pipeline of our json-compiler (although
we did not bother to call it thus) yields the json-data in form of Python-objects.
Now let's assume, we'd like to add two further processing stages, one which yields
the json-data as a human-readable pretty-printed json-string, 
the other which yields it as a compact bytearry, ready for transmission over
some kind of connection. This is how our extension of the standard-pipeline looks 
like::

            |
      -------------  pretty-print  -----------------------
      | json-data |--------------->| human readable json |
      -------------                -----------------------
            |
            |--- compact-print
            |
    -----------------
    | one-line json |
    -----------------
            |
            |--- bytearry-convert
            |
   --------------------
   | transmission obj |
   --------------------

Let's define the necessary junctions "pretty-print", "compact-print" and
"bytearray-convert". Each junction is a 3-tuple of 1) the name of input stage, 2)
a compilation functions that either transforms the input-tree produces some
other kind of output and 3) the name of the output stage.

A restriction of junctions in DHParser consists in the fact that the input data
for the compilation functions must always be the root-node of a tree. This
restriction is due to the fact that the standard case for
transformation-pipelines in the Digital Humanities is that of chains of
tree-transformations. However, in some cases, as in this example, the data
already has a different form than a tree at earlier stages of the pipeline. In
order to cover those cases, DHParser uses the trick to attach the data to the
root-node of the last tree stage and then passing the root-node with the
attached data to the next junction. The RootNode thus serves as a pod for
passing the non-tree data further on through the data. This trick has the
benefit that the methods for error reporting that the
:py:class:`DHParser.nodetree.RootNode`-class provides can also be used for the
non-tree-stages of the pipeline. In our example already the first stage of the
extended data is not a nodetree, any more. So we need to attach it to the
root-node of the last tree-stage, which in this case is the AST::

   >>> ast.data = json_objs
   >>> source_stages = {'json': ast}

Now let's define the "pretty-print"-compilation function and the respective junction::

   >>> import json
   >>> from DHParser.nodetree import RootNode
   >>> def pretty_print(input: RootNode) -> str:
   ...     try:
   ...         return json.dumps(input.data, indent=2)
   ...     except TypeError as e:
   ...         input.new_error(input, "JSON-Error: " + str(e))
   >>> pretty_print_junction = ('json', lambda : pretty_print, 'pretty-json')

Any errors can simply be attached to the RootNode-obeject that is passed to the
compilation-function!

Since "pretty_print" yields a final state, it does not need to return a tree, but it may
yield any data-type. This is different for the intermediary junction "compact-print".
Here, the transformed data must be attached to the RootNode, again::

   >>> def compact_print(input: RootNode) -> RootNode:
   ...     try:
   ...         input.data = json.dumps(input.data)
   ...     except TypeError as e:
   ...         input.new_error(input, "JSON-Error: " + str(e))
   ...     return input
   >>> compact_print_junction = ('json', lambda : compact_print, 'compact-json')

The "byte-array"-convert-junction that takes the output from the last step, the
compact-json, as input can be defined as follows::

   >>> def bytearray_convert(input: RootNode) -> bytes:
   ...     return input.data.encode('utf-8')
   >>> bytearray_convert_junction = ('compact-json', lambda : bytearray_convert, 'byte-stream')

Finally, all junctions must be passed to the :py:func:`~compile.run_pipeline`-function
which automatically constructs the bifurcated pipeline from the given junctions and passes
the input-data through all bifurcations of the pipeline::

   >>> from DHParser.compile import run_pipeline
   >>> target_stages={"pretty-json", "byte-stream"}
   >>> results = run_pipeline({pretty_print_junction, compact_print_junction,
   ...                         bytearray_convert_junction},
   ...                         source_stages, target_stages)

Note, that ``source_stages`` is a mapping the of source-stage-names to the
source-stage's data, while ``target-stages`` is merely a set of names of all
final stages.

The results are a mapping of all target AND intermediary stages to 2-tuples of
the output-data of the respective stage (or None, if any fatal error has
occurred) and a potentially empty error list::

   >>> for target in sorted(list(target_stages)):
   ...    print(target, results[target][0])
   byte-stream b'{"test": ["This", "is", 1.0, "JSON", "test"]}'
   pretty-json {
     "test": [
       "This",
       "is",
       1.0,
       "JSON",
       "test"
     ]
   }

A nice feature of extended pipelines is their integration with the
testing-framework (see :py:mod:`~testing`): All stages of an extended pipeline
can be unit-tested with DHParser's unit-testing framework for grammars as long
as the results of these stages can be serialized with ``str()``.


*Classes and Functions-Reference*
---------------------------------

The full documentation of all classes and functions can be found in module
:py:mod:`DHParser.compile`. The following table of contents lists the most
important of these:

class Compile
^^^^^^^^^^^^^

* :py:class:`~compile.Compiler`: A callable base class for compilers. Derive
      from this class and fill in ``on_NAME(self, node)`` and ``attr_NAME(self,
      node, value)`` methods to build a compiler.

  * :py:attr:`~compile.Compiler.path`: During compilation the current path to
        the node that is about to be compiled.

  * :py:attr:`~compile.Compiler.finalizers`: A list of pairs of callables and
        arguments, that will be called at the end of the compilation of the
        entire tree.

  * :py:meth:`~compile.Compiler.prepare`: An overrideable method that will be
        called with the root-note just before the compilation of the tree
        starts.

  * :py:meth:`~compile.Compiler.finalize`: A overrideable method that will be
        called with the result and that may return a possibly modified result
        after the compilation has finished.

  * :py:meth:`~compile.Compiler.wildcard`: An overriable commpilaiton-method
        that will be called when no specific compilation method, i.e.
        ``on_NAME(node)`` has been defined. It defaults to redirecting to
        :py:meth:`~compile.Commpiler.fallback_compiler`.

   * :py:meth:`~compile.Compiler.fallback_compiler`: A method that will be
        be called on nodes for the type or name, for that matter, of which
        no ``on_NME(onde)``-method has been defined. This method should ony
        be called for purely tree-transforming Comilper objects.

Types and Functions
^^^^^^^^^^^^^^^^^^^

   * :py:data:`~compile.Copiler.CompilationResult`: A named tuple-type that stores
        the result of a compilation: (result: Any, messages: list[:py:class:`~error.Error``], AST: Optioal[:py:class:`~nodetree.RootNode`])

   * :py:func:`compile.compile_source`: A functions that calls preprocessor, parser, 
        transformer and compiler in sequence on a source text. In other words, it
        runs the "standard-pipeline" on the source text.

   * :py:func:`compile.process_tree`: Calls a compiler on a given tree only if
        the tree does not already had any fatal errors in a previous processing
        stage. This function is syntactic sugar to allow allow writing sequences
        of transformation or compilation stages as a sequence of
        ``process_tree()``-calls without the need to chain them with if clauses.

   * :py:data:`~compile.Junction`: A type-alias for a tuple: (name of relative
        source stage, factory for a compiler, name of the relative destination
        stage). "relative" here means from the point of view of the compilation
        function returned by the factory.

   * :py:func:`~compile.run_pipeline`: Runs an extended pipeline of compilation or
        transformation functions (or, more precisely, callables) that is definied
        by a set of junctions and returns the results for selected target stages.  
