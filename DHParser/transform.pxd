#cython: infer_types=True
#cython: language_level=3
#cython: c_string_type=unicode
#cython: c_string_encoding=utf-8

import cython

# any functions that causes trouble with cython has been commented out!

# cpdef transformation_factory(t1=?, t2=?, t3=?, t4=?, t5=?)
# cpdef type_guard(t)
# cpdef decorator(f)
# cpdef gen_special(*args)
# cpdef gen_partial(*args, **kwargs)
cpdef key_tag_name(node: Node)
# cpdef traverse(root_node: Node, processing_table: ProcessingTableType,
#               key_func: KeyFunc = ?)
# cpdef traverse_recursive(context)
# cpdef traverse_locally(context: List[Node], processing_table: Dict,
#                       key_func: Callable = ?)
# cpdef apply_if(context: List[Node], transformation: Callable, 
#                condition: Callable)
# cpdef apply_unless(context: List[Node], transformation: Callable,
#                  condition: Callable)
cpdef is_single_child(context: List[Node])
cpdef is_named(context: List[Node])
cpdef is_anonymous(context: List[Node])
cpdef contains_only_whitespace(context: List[Node])
cpdef is_empty(context: List[Node])
# cpdef is_token(context: List[Node], tokens: AbstractSet[str] = ?)
# cpdef is_one_of(context: List[Node], tag_name_set: AbstractSet[str])
# cpdef not_one_of(context: List[Node], tag_name_set: AbstractSet[str])
# cpdef matches_re(context: List[Node], patterns: AbstractSet[str])
# cpdef has_content(context: List[Node], regexp: str)
# cpdef has_ancestor(context: List[Node], tag_name_set: AbstractSet[str])
cpdef _replace_by(node: Node, child: Node)
cpdef _reduce_child(node: Node, child: Node)
cpdef replace_by_single_child(context: List[Node])
cpdef reduce_single_child(context: List[Node])
# cpdef replace_or_reduce(context: List[Node], condition: Callable = ?)
# cpdef change_tag_name(context: List[Node], name: str)
# cpdef flatten(context: List[Node], condition: Callable = ?,
#               recursive: bool = ?)
cpdef collapse(context: List[Node])
# cpdef collapse_children_if(context: List[Node], condition: Callable,
#                   target_tag: ParserBase)
# cpdef close_package()
# cpdef transform_content(context: List[Node], func: Callable)
# cpdef replace_content_with(context: List[Node], content: str)
cpdef normalize_whitespace(context)
# cpdef merge_whitespace(context)
# cpdef move_adjacent(context, condition: Callable = ?)
## cpdef lstrip(context: List[Node], condition: Callable = ?)
## cpdef rstrip(context: List[Node], condition: Callable = ?)
## cpdef strip(context: List[Node], condition: Callable = ?)
# cpdef keep_children(context: List[Node], section: slice)
# cpdef keep_children_if(context: List[Node], condition: Callable)
# cpdef keep_tokens(context: List[Node], tokens: AbstractSet[str] = ?)
# cpdef keep_nodes(context: List[Node], tag_names: AbstractSet[str])
# cpdef keep_content(context: List[Node], regexp: str)
# cpdef remove_children_if(context: List[Node], condition: Callable)
# cpdef remove_brackets(context: List[Node])
# cpdef remove_tokens(context: List[Node], tokens: AbstractSet[str] = ?)
# cpdef remove_children(context: List[Node], tag_names: AbstractSet[str])
# cpdef remove_content(context: List[Node], regexp: str)
# cpdef error_on(context: List[Node], condition: Callable,
#              error_msg: str, error_code: ErrorCode)
# cpdef assert_content(context: List[Node], regexp: str)
# cpdef require(context: List[Node], child_tags: AbstractSet[str])
# cpdef forbid(context: List[Node], child_tags: AbstractSet[str])
cpdef peek(context: List[Node])