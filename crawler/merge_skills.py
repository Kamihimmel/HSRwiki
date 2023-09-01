# coding: utf-8

import json
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fields = ['id', 'ENname', 'CNname', 'JAname', 'stype', 'maxlevel', 'weaknessbreak', 'energyregen', 'levelmultiplier',
          'tags']

skills = []
with open(base_dir + '/lib/characterlist.json', 'r', encoding='utf-8') as f:
    data = json.load(f)['data']
for d in data:
    with open(base_dir + '/' + d['infourl'], 'r', encoding='utf-8') as j:
        data = json.load(j)
        if 'skilldata' in data and data['skilldata'] is not None:
            for s in data['skilldata']:
                if 'tags' not in s or 'effect' not in s:
                    continue
                effect_list = list(
                    filter(lambda e: 'type' in e and 'iid' in e and (e['type'] == 'buff' or e['type'] == 'debuff'), s['effect']))
                if len(effect_list) == 0:
                    continue
                d = {'characterid': data['id']}
                for field in fields:
                    if field in s:
                        d[field] = s[field]
                d['effect'] = effect_list
                skills.append(d)
skills.sort(key=lambda sk: sk['characterid'])
result = {'data': skills}
with open(base_dir + '/lib/skilllist.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(result, ensure_ascii=False, skipkeys=True, indent=4))
