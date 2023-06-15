from DHParser import grammar_provider

class TestLateBinding:
    def test_late_binding(self):
        lang = """
            document = allof
            @ allof_error = '{} erwartet, {} gefunden :-('
            @ allof_skip = "D", "E", "F", "G"
            allof = "A" ° "B" ° §"C" ° "D" ° "E" ° "F" ° "G" 
        """
        gr = grammar_provider(lang)()