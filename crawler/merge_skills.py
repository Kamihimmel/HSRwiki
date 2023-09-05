# coding: utf-8

import json
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
skill_fields = ['skilldata', 'tracedata', 'eidolon']
fields = ['id', 'ENname', 'CNname', 'JAname', 'stype', 'maxlevel', 'weaknessbreak', 'energyregen', 'levelmultiplier',
          'tags']

def valid_ally_buff(e):
    if 'type' not in e or 'iid' not in e or 'tag' not in e:
        return False
    if e['type'] == 'buff':
        return 'allally' in e['tag'] or 'singleally' in e['tag']
    elif e['type'] == 'debuff':
        return 'allenemy' in e['tag'] or 'singleenemy' in e['tag']
    return False

skills = []
with open(base_dir + '/lib/characterlist.json', 'r', encoding='utf-8') as f:
    data = json.load(f)['data']
for d in data:
    with open(base_dir + '/' + d['infourl'], 'r', encoding='utf-8') as j:
        c_data = json.load(j)
        for s_field in skill_fields:
            if s_field in c_data and c_data[s_field] is not None:
                for s in c_data[s_field]:
                    if 'tags' not in s or 'effect' not in s:
                        continue
                    effect_list = list(filter(valid_ally_buff, s['effect']))
                    if len(effect_list) == 0:
                        continue
                    d = {'characterid': c_data['id']}
                    for field in fields:
                        if field in s:
                            d[field] = s[field]
                    d['effect'] = effect_list
                    skills.append(d)
skills.sort(key=lambda sk: sk['characterid'])
result = {'data': skills}
with open(base_dir + '/lib/skilllist.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps(result, ensure_ascii=False, skipkeys=True, indent=4))
