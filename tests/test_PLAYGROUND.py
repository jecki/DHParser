
from DHParser import grammar_provider, is_logging, log_ST, is_error, log_parsing_history, get_config_value, set_config_value

# class TestSomething:
#     def test_very_simple(self):
#         minilang = """
#             term = term (`*`|`/`) factor | factor
#             factor = /[0-9]+/
#             """
#         save = get_config_value('static_analysis')
#         set_config_value('static_analysis', False)
#         grammar_factory = grammar_provider(minilang)
#         parser = grammar_factory()
#         # print(parser.python_src__)
#         snippet = "5*4*3*2"
#         # set_tracer(parser, trace_history)
#         st = parser(snippet)
#         if is_logging():
#             log_ST(st, "test_LeftRecursion_very_simple.cst")
#             log_parsing_history(parser, "test_LeftRecursion_very_simple")
#         assert not is_error(st.error_flag), str(st.errors)
#         st = parser("1*2*3*4*5*6*7*8*9")
#         # if is_logging():
#         #     log_ST(st, 'test_LeftRecursion_very_simple_2.cst')
#         #     log_parsing_history(parser, 'test_LeftRecursion_very_simple_2')
#         assert not is_error(st.error_flag)
#         set_config_value('static_analysis', save)

class TestSomething:
    def test_lr_spezial(self):
        grammar = grammar_provider("""
            BelegText = /"/~ BelegKern /"/~
            BelegKern = { '(' BelegKern ')' | '+' }
            """)()
        result = grammar('""')
        print(result.as_sxpr())