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
name_lang_mapping = {'EN': 'ENname', 'CN': 'CNname', 'JP': 'JAname'} # why does it start with JA for JP localization?
set_effect_mapping = {'EN': ' Set Effect', 'CN': '件套装效果', 'JP': 'セット効果'}
ua = UserAgent() # required for non-browser http request, or you will get a response code of 403
result = {}

def append_name(soup_dict):
    for lang in languages:
        result[name_lang_mapping[lang]] = soup_dict[lang].select_one('h2.wp-block-post-title').text
        print('append %s name: %s' % (lang, result[name_lang_mapping[lang]]))

def append_image(lightcone, lightcone_id):
    path = 'images/relics/%s.webp' % lightcone_id
    result['imageurl'] = path
    with open(base_dir + '/' + path, 'wb') as f:
        url = 'https://hsr.honeyhunterworld.com/img/relic_set/%s-relic_set_icon.webp' % lightcone
        res = requests.get(url, headers={'User-Agent': ua.random}, timeout=30)
        f.write(res.content)
    print('append image: %s' % path)

def append_basic(relic, relic_id, soup_dict):
    soup = soup_dict['EN']
    main_trs = soup.select('table.genshin_table.main_table > tr')
    set_num = len(main_trs) - 2
    result['set'] = str(set_num)
    print('append set_num: %s' % set_num)
    for i in range(1, set_num + 1):
        children = main_trs[i].contents
        part = children[0].text.lower()
        part_name = children[1].contents[1].contents[0].contents[0].text
        path = 'images/relics/IconRelic_%s_%s.webp' % (relic_id, i if set_num == 4 else i + 4)
        result[re.sub(r'^.*?\s+', '', part)] = path
        with open(base_dir + '/' + path, 'wb') as f:
            url = 'https://hsr.honeyhunterworld.com/img/item/%s-item_icon.webp' % util.clean_name(part_name)
            res = requests.get(url, headers={'User-Agent': ua.random}, timeout=30)
            f.write(res.content)
        print('append %s image: %s' % (part, path))

'''
skill start
'''
def append_skill_name_and_desc(cur_skill, skill_dict, index):
    desc_dict = {}
    for lang in languages:
        name_desc = skill_dict[lang][index].split(': ')
        cur_skill[name_lang_mapping[lang]] = name_desc[0][0] + set_effect_mapping[lang]
        desc_dict['Description' + lang] = name_desc[1]
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

def append_skill_tags(cur_skill, skill_dict, index):
    tags = []
    cur_skill['tags'] = tags

def append_skill_effect(cur_skill, skill_dict, index):
    effect = []
    cur_skill['effect'] = effect

def append_skill(soup_dict):
    skilldata = []
    skill_dict = {}
    for lang in languages:
        main_trs = soup_dict[lang].select('table.genshin_table.main_table > tr')
        set_effect = main_trs[len(main_trs) - 1]
        skills = []
        for i in range(0, 1):
            skill_desc = ''
            for el in set_effect.contents[1].contents:
                if el.name == 'br':
                    skills.append(skill_desc)
                    skill_desc = ''
                else:
                    skill_desc += el.text
            skills.append(skill_desc)
        skill_dict[lang] = skills
    skill_cnt = len(list(skill_dict['EN']))
    for i in range(0, skill_cnt):
        cur_skill = {}
        append_skill_name_and_desc(cur_skill, skill_dict, i)
        append_skill_attr(cur_skill, skill_dict, i)
        append_skill_tags(cur_skill, skill_dict, i)
        append_skill_effect(cur_skill, skill_dict, i)
        skilldata.append(cur_skill)
    result['skilldata'] = skilldata
'''
skill end
'''

# main function
def genrate_json(relic):
    print('generate lib json from honeyhunterworld for: %s' % relic)
    soup_dict = {}
    for lang in languages:
        url = 'https://hsr.honeyhunterworld.com/%s-relic_set/?lang=%s' % (relic, lang)
        res = requests.get(url, headers={'User-Agent': ua.random}, timeout=10)
        soup_dict[lang] = BeautifulSoup(res.text, 'html.parser')
        if soup_dict[lang] is None or soup_dict[lang].select_one('h2.wp-block-post-title') is None:
            print('fetch failed, please try again')
            exit(1)
    with open(base_dir + '/lib/reliclist.json', 'r', encoding='utf-8') as f:
        relic_info = json.load(f)
        result['id'] = list(filter(lambda i: i['ENname'].replace('(WIP)', '').lower().replace(' ', '-') == relic, relic_info['data']))[0]['id']
    append_name(soup_dict)
    append_image(relic, result['id'])
    append_basic(relic, result['id'], soup_dict)
    append_skill(soup_dict)
    with open(base_dir + '/lib/relics/' + result['id'] + '.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(result, ensure_ascii=False, skipkeys=True, indent=4))


if __name__ == '__main__':
    genrate_json(sys.argv[1])
