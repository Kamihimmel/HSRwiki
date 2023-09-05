# coding: utf-8

import json
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(base_dir + '/lib/characterlist.json', 'r', encoding='utf-8') as f:
    data = json.load(f)['data']
for d in data:
    with open(base_dir + '/' + d['infourl'], 'r', encoding='utf-8') as j:
        c_data = json.load(j)
        if 'eidolon' in c_data and c_data['eidolon'] is not None:
            for s in c_data['eidolon']:
                s['id'] = '%s-%s' % (s['id'], s['eidolonnum'])
    with open(base_dir + '/' + d['infourl'], 'w', encoding='utf-8') as f:
        f.write(json.dumps(c_data, ensure_ascii=False, skipkeys=True, indent=4))