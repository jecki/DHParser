import sys, os, datetime


mlw_root_dir = os.path.join('..', '..', 'MLW-DSL')
mlw_files_dir = os.path.join("Beispiele", "Fasz53MLWDateien")

os.chdir(mlw_root_dir)
print(os.listdir())

from DHParser.compile import compile_source
from DHParser.error import CANCELED

sys.path.append('.')
from MLWParser import get_preprocessor, get_grammar

def collect_mlw_files():
    mlw_files = []
    for path, dirs, files in os.walk(mlw_files_dir):
        for f in files:
            if f.lower().endswith('.mlw'):
                with open(os.path.join(path, f), 'r', encoding='utf-8') as mlw_file:
                    data = mlw_file.read()
                mlw_files.append((f, data))
    mlw_files.sort(key=lambda k: k[0].lower())
    return mlw_files


def parse_mlw_files(mlw_files, preprocessor, grammar):
    time = datetime.datetime.now()
    for name, data in mlw_files:
        _ = compile_source(data, preprocessor, grammar, lambda rn: rn, lambda rn: rn)
        t2 = datetime.datetime.now()
        print(name, t2 - time)
        time = t2


if __name__ == '__main__':
    mlw_files = collect_mlw_files()
    preprocessor = get_preprocessor()
    grammar = get_grammar()
    time1 = datetime.datetime.now()
    parse_mlw_files(mlw_files, preprocessor, grammar)
    time2 = datetime.datetime.now()
    print(time2 - time1)