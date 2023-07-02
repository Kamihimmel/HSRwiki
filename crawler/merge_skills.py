# coding: utf-8

import json
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ignores = ['skilllist.json', 'lightconelist.json', 'reliclist.json', 'characterlist.json', 'lightcones', 'relics']

skills = []
for f in os.listdir(base_dir + '/lib'):
    if f in ignores or not os.path.exists(base_dir + '/lib/' + f):
        continue
    with open(base_dir + '/lib/' + f, 'r', encoding='utf-8') as j:
        data = json.load(j)
        if 'skilldata' in data and data['skilldata'] is not None:
            for s in data['skilldata']:
                d = {'characterid': data['id']}
                skills.append(d | s)
result = {'data': skills}
with open(base_dir + '/lib/skilllist.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(result, ensure_ascii=False, skipkeys=True, indent=4))
