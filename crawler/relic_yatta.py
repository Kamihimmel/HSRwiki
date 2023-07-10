# coding: utf-8

import json
import os
import re
import requests
import sys

import util

from fake_useragent import UserAgent

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # absolute path of repo dir
languages = ['EN', 'CN', 'JP']
name_lang_mapping = {'EN': 'ENname', 'CN': 'CNname', 'JP': 'JAname'}
part_mapping = {'hand': 'hands', 'foot': 'feet', 'neck': 'sphere', 'object': 'rope'}
set_effect_mapping = {'EN': ' Set Effect', 'CN': '件套装效果', 'JP': 'セット効果'}
ua = UserAgent()  # required for non-browser http request, or you will get a response code of 403
result = {}


def append_name(data_dict):
    for lang in languages:
        result[name_lang_mapping[lang]] = data_dict[lang]['name']
        print('append %s name: %s' % (lang, result[name_lang_mapping[lang]]))


def append_image(relic_icon):
    img_ext = 'png'
    path = 'images/relics/%s' % relic_icon
    util.download_yatta_image('crawler/yatta/' + path, 'relic', relic_icon, img_ext, base_dir)
    result['imageurl'] = '%s.%s' % (path, img_ext)
    print('append image: %s' % path)


def append_basic(data_dict):
    suite = data_dict['EN']['suite']
    set_num = len(suite)
    result['set'] = str(set_num)
    print('append set_num: %s' % set_num)
    for k, v in suite.items():
        p = k.lower()
        part = part_mapping[p] if p in part_mapping else p
        icon = v['icon']
        img_ext = 'png'
        path = 'images/relics/%s' % icon
        util.download_yatta_image('crawler/yatta/' + path, 'relic', icon, img_ext, base_dir)
        result[re.sub(r'^.*?\s+', '', part)] = '%s.%s' % (path, img_ext)
        print('append %s image: %s' % (part, path))


'''
skill start
'''


def append_skill_name_and_desc(cur_skill, skill_dict, key):
    desc_dict = {}
    for lang in languages:
        cur_skill[name_lang_mapping[lang]] = key + set_effect_mapping[lang]
        desc = util.clean_desc_yatta(skill_dict[lang][key]['description'])
        for k, v in skill_dict[lang][key]['params'].items():
            desc = desc.replace('[%s]' % k, str(util.format_percent_number(v[0]) if '[%s]%%' % k in desc else v[0]))
        desc_dict['Description' + lang] = desc
        print('append skill %s name: %s' % (lang, cur_skill[name_lang_mapping[lang]]))
    for k, v in desc_dict.items():
        cur_skill[k] = v
        print('append skill %s desc: %s' % (k, v))


def append_skill_attr(cur_skill, skill_dict, index):
    buffskill = util.is_buff_skill(cur_skill['DescriptionEN'])
    teamskill = util.is_team_skill(cur_skill['DescriptionEN'])
    cur_skill['buffskill'] = buffskill
    cur_skill['teamskill'] = teamskill
    print('append skill buffskill: %s, teamskill: %s' % (buffskill, teamskill))


def append_skill_tags(cur_skill, exist_skill):
    cur_skill['tags'] = exist_skill['tags'] if 'tags' in exist_skill else []


def append_skill_effect(cur_skill, exist_skill):
    cur_skill['effect'] = exist_skill['effect'] if 'effect' in exist_skill else []


def compare_skill(s, d):
    if 'id' in s and 'id' in d:
        return s['id'] == d['id']
    return s['ENname'] == d['ENname']


def append_skill(data_dict, exist_dict):
    skilldata = []
    skill_dict = {}
    for lang in languages:
        skill_dict[lang] = data_dict[lang]['skillList']
    exist_skills = exist_dict['skilldata']
    for key in skill_dict['EN'].keys():
        cur_skill = {}
        append_skill_name_and_desc(cur_skill, skill_dict, key)
        append_skill_attr(cur_skill, skill_dict, key)
        find = list(filter(lambda s: compare_skill(s, cur_skill), exist_skills))
        exist_skill = find[0] if len(find) > 0 else {}
        append_skill_tags(cur_skill, exist_skill)
        append_skill_effect(cur_skill, exist_skill)
        skilldata.append(cur_skill)
    result['skilldata'] = skilldata
    print('append skilldata, count: %s' % len(skilldata))


'''
skill end
'''


# main function
def generate_json(relic):
    util.prepare_dirs('yatta', base_dir)
    print('generate lib json from yatta for: %s' % relic)
    with open(base_dir + '/lib/reliclist.json', 'r', encoding='utf-8') as f:
        relic_info = json.load(f)
        result['id'] = list(
            filter(lambda i: i['ENname'].replace('(WIP)', '').lower().replace(' ', '-') == relic.lower(),
                   relic_info['data']))[0]['id']
    with open(base_dir + '/lib/relics/%s.json' % result['id'], 'r', encoding='utf-8') as f:
        exist_dict = json.load(f)
    data_dict = {}
    for lang in languages:
        url = 'https://api.yatta.top/hsr/v2/%s/relic/%s' % (lang, result['id'])
        res = requests.get(url, headers={'User-Agent': ua.edge}, timeout=(10, 30))
        data = json.loads(res.content)
        if data is None or 'response' not in data or data['response'] != 200:
            print('fetch failed, please try again')
            exit(1)
        data_dict[lang] = data['data']
    append_name(data_dict)
    append_image(data_dict['EN']['icon'])
    append_basic(data_dict)
    append_skill(data_dict, exist_dict)
    with open(base_dir + '/crawler/yatta//lib/relics/' + result['id'] + '.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(result, ensure_ascii=False, skipkeys=True, indent=4))


if __name__ == '__main__':
    generate_json(sys.argv[1])
