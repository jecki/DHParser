import sys
print('sys.path:')
for p in sys.path:
    print(p)

print('')
print('PYTHONPATH')
import os
if "PYTHONPATH" in os.environ:
    print(os.environ['PYTHONPATH'])
else:
    print('PYTHONPATH not set')

