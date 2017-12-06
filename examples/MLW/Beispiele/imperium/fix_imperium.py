# TODO: Schreibe Skript um die Anführungsstriche in imperium.mlw hinzu zu fügen

import re

with open('imperium.mlw') as f:
    imperium = f.read()

# m = re.search('\*.*\d\s*(.*\n)', imperium)
for match in re.finditer('\*.*\d[ .]\s*([^Z\n;]*)(?:\n| ZUSATZ)', imperium):
    print(match.group(1))

