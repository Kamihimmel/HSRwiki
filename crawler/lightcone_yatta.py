# coding: utf-8

import json
import os
import re
import requests
import sys

import util

from bs4 import BeautifulSoup
from fake_useragent import UserAgent

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # absolute path of repo dir
languages = ['EN', 'CN', 'JP']
name_lang_mapping = {'EN': 'ENname', 'CN': 'CNname', 'JP': 'JAname'}
ua = UserAgent() # required for non-browser http request, or you will get a response code of 403
result = {}

def append_name(data_dict):
    for lang in languages:
        result[name_lang_mapping[lang]] = data_dict[lang]['name']
        print('append %s name: %s' % (lang, result[name_lang_mapping[lang]]))

def append_image(lightcone_id):
    path = 'images/lightcones/%s.png' % lightcone_id
    result['imageurl'] = path
    with open(base_dir + '/' + path, 'wb') as f:
        url = 'https://api.yatta.top/hsr/assets/UI/equipment/medium/%s.png' % lightcone_id
        res = requests.get(url, headers={'User-Agent': ua.random}, timeout=30)
        f.write(res.content)
    print('append image: %s' % path)

def append_image_large(lightcone_id):
    path = 'images/lightcones/%sl.png' % lightcone_id
    result['imagelargeurl'] = path
    with open(base_dir + '/' + path, 'wb') as f:
        url = 'https://api.yatta.top/hsr/assets/UI/equipment/large/%s.png' % lightcone_id
        res = requests.get(url, headers={'User-Agent': ua.random}, timeout=30)
        f.write(res.content)
    print('append large image: %s' % path)

def append_basic(data_dict):
    result['wtype'] = data_dict['EN']['types']['pathType']['name'].lower()
    result['rarity'] = str(data_dict['EN']['rank'])
    print('append wtype: %s, rarity: %s' % (result['wtype'], result['rarity']))

def append_level(data_dict):
    upgrade = data_dict['EN']['upgrade']
    leveldata = []
    for i in range(0, len(upgrade)):
        lvl = upgrade[i]
        lvl_incr = lvl['maxLevel'] - 1
        if i == 0:
            leveldata.append({
                'level': "1",
                'hp': lvl['skillBase']['hPBase'],
                'atk': lvl['skillBase']['attackBase'],
                'def': lvl['skillBase']['defenceBase'],
            })
        leveldata.append({
            'level': str(lvl['maxLevel']),
            'hp': float(round(lvl['skillBase']['hPBase'] + lvl['skillAdd']['hPAdd'] * lvl_incr, 2)),
            'atk': float(round(lvl['skillBase']['attackBase'] + lvl['skillAdd']['attackAdd'] * lvl_incr, 2)),
            'def': float(round(lvl['skillBase']['defenceBase'] + lvl['skillAdd']['defenceAdd'] * lvl_incr, 2)),
        })
        if i < len(upgrade) - 1:
            next_lvl = upgrade[i + 1]
            leveldata.append({
                'level': str(lvl['maxLevel']) + '+',
                'hp': float(round(next_lvl['skillBase']['hPBase'] + lvl['skillAdd']['hPAdd'] * lvl_incr, 2)),
                'atk': float(round(next_lvl['skillBase']['attackBase'] + lvl['skillAdd']['attackAdd'] * lvl_incr, 2)),
                'def': float(round(next_lvl['skillBase']['defenceBase'] + lvl['skillAdd']['defenceAdd'] * lvl_incr, 2)),
            })
    result['leveldata'] = leveldata

'''
skill start
'''
def append_skill_name(cur_skill, skill_dict):
    for lang in languages:
        cur_skill[name_lang_mapping[lang]] = skill_dict[lang]['name']
        print('append skill %s name: %s' % (lang, cur_skill[name_lang_mapping[lang]]))

def append_skill_desc(cur_skill, skill_dict):
    for lang in languages:
        cur_skill['Description' + lang] = util.clean_desc_yatta(skill_dict[lang]['description'])
        print('append skill %s desc: %s' % (lang, cur_skill['Description' + lang]))

def append_skill_attr(cur_skill, skill_dict):
    skill_en = skill_dict['EN']
    buffskill = util.is_buff_skill(cur_skill['DescriptionEN'])
    teamskill = util.is_team_skill(cur_skill['DescriptionEN'])
    cur_skill['maxlevel'] = 5
    cur_skill['buffskill'] = buffskill
    cur_skill['teamskill'] = teamskill
    print('append skill maxlevel: %s, buffskill: %s, teamskill: %s' % (cur_skill['maxlevel'], buffskill, teamskill))
    
def append_skill_levelmultiplier(cur_skill, skill_dict):
    desc = cur_skill['DescriptionEN']
    params = skill_dict['EN']['params']
    levelmultiplier = []
    for i, multi in params.items():
        percent = ('[%s]%%' % i) in desc
        d = {}
        for j in range(0, len(multi)):
            d[str(j + 1)] = util.format_percent_number(multi[j]) if percent else multi[j]
        levelmultiplier.append(d)
    cur_skill['levelmultiplier'] = levelmultiplier

def append_skill_tags(cur_skill, skill_dict):
    tags = []
    cur_skill['tags'] = tags

def append_skill_effect(cur_skill, skill_dict):
    effect = []
    cur_skill['effect'] = effect

def append_skill(data_dict):
    skilldata = []
    skill_dict = {}
    for lang in languages:
        skill_dict[lang] = data_dict[lang]['skill']
    cur_skill = {}
    append_skill_name(cur_skill, skill_dict)
    append_skill_desc(cur_skill, skill_dict)
    append_skill_attr(cur_skill, skill_dict)
    append_skill_levelmultiplier(cur_skill, skill_dict)
    append_skill_tags(cur_skill, skill_dict)
    append_skill_effect(cur_skill, skill_dict)
    skilldata.append(cur_skill)
    result['skilldata'] = skilldata
'''
skill end
'''

# main function
def genrate_json(lightcone):
    print('generate lib json from honeyhunterworld for: %s' % lightcone)
    with open(base_dir + '/lib/lightconelist.json', 'r', encoding='utf-8') as f:
        lightcone_info = json.load(f)
        result['id'] = list(filter(lambda i: i['ENname'].replace('(WIP)', '').lower().replace(' ', '-') == lightcone.lower(), lightcone_info['data']))[0]['id']
    data_dict = {}
    for lang in languages:
        url = 'https://api.yatta.top/hsr/v2/%s/equipment/%s' % (lang, result['id'])
        res = requests.get(url, headers={'User-Agent': ua.random}, timeout=10)
        data = json.loads(res.content)
        if data is None or 'response' not in data or data['response'] != 200:
            print('fetch failed, please try again')
            exit(1)
        data_dict[lang] = data['data']
    append_name(data_dict)
    append_image(result['id'])
    append_image_large(result['id'])
    append_basic(data_dict)
    append_level(data_dict)
    append_skill(data_dict)
    with open(base_dir + '/lib/lightcones/' + result['id'] + '.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(result, ensure_ascii=False, skipkeys=True, indent=4))


if __name__ == '__main__':
    genrate_json(sys.argv[1])
