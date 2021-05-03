with open('tutorial_json_data.json', 'r') as f:
    data = f.read()

for i in range(100):
    f =  open('tutorial_json_data_%i.json' % i, 'w')
    f.write(data)
    f.close()
