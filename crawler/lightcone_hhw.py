# coding: utf-8

import json
import os
import re
import requests
import sys

from bs4 import BeautifulSoup
from fake_useragent import UserAgent

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # absolute path of repo dir
languages = ['EN', 'CN', 'JP']
name_lang_mapping = {'EN': 'ENname', 'CN': 'CNname', 'JP': 'JAname'} # why does it start with JA for JP localization?
ua = UserAgent() # required for non-browser http request, or you will get a response code of 403
result = {}

def append_name(soup_dict):
    for lang in languages:
        result[name_lang_mapping[lang]] = soup_dict[lang].select_one('h2.wp-block-post-title').text
        print('append %s name: %s' % (lang, result[name_lang_mapping[lang]]))

def append_image(lightcone, lightcone_id):
    path = 'images/lightcones/%s.webp' % lightcone_id
    result['imageurl'] = path
    with open(base_dir + '/' + path, 'wb') as f:
        url = 'https://hsr.honeyhunterworld.com/img/item/%s-item_icon.webp' % lightcone
        res = requests.get(url, headers={'User-Agent': ua.random}, timeout=30)
        f.write(res.content)
    print('append image: %s' % path)

def append_image_large(lightcone, lightcone_id):
    path = 'images/lightcones/%sl.webp' % lightcone_id
    result['imagelargeurl'] = path
    with open(base_dir + '/' + path, 'wb') as f:
        url = 'https://hsr.honeyhunterworld.com/img/item/%s-item_icon_figure.webp' % lightcone
        res = requests.get(url, headers={'User-Agent': ua.random}, timeout=30)
        f.write(res.content)
    print('append large image: %s' % path)

def append_basic(soup_dict):
    soup = soup_dict['EN']
    wtype = None
    rarity = None
    main_trs = soup.select('table.genshin_table.main_table > tr')
    for tr in main_trs:
        children = tr.contents
        if children[0].text == 'Rarity':
            rarity = str(len(children[1].contents))
        elif children[0].text == 'Path':
            wtype = children[1].text.lower().strip()
    result['wtype'] = wtype
    result['rarity'] = rarity
    print('append wtype: %s, rarity: %s' % (wtype, rarity))

def append_level(soup_dict):
    soup = soup_dict['EN']
    leveldata = []
    stats_trs = soup.select('table.genshin_table.stat_table > tr')
    for tr in stats_trs:
        children = tr.contents
        if len(children) < 3:
            continue
        level = children[0].text
        leveldata.append({
            'level': level,
            'hp': int(children[3].text),
            'atk': float(children[1].text) if '.' in children[1].text else int(children[1].text),
            'def': float(children[2].text) if '.' in children[2].text else int(children[2].text),
        })
    result['leveldata'] = leveldata
    print('append leveldata, count: %s' % len(leveldata))

'''
util function start
'''
def is_buff_skill(desc):
    return ' increases ' in desc or ' increase ' in desc or ' gain ' in desc

def is_team_skill(desc):
    return False
'''
util function end
'''

'''
skill start
'''
def append_skill_name(cur_skill, skill_dict, index):
    for lang in languages:
        cur_skill[name_lang_mapping[lang]] = skill_dict[lang][index].contents[0].contents[1].text
        print('append skill %s name: %s' % (lang, cur_skill[name_lang_mapping[lang]]))

def append_skill_desc(cur_skill, skill_dict, index):
    for lang in languages:
        skill_content = skill_dict[lang][index].contents[1].contents[0].contents
        skill_desc = ''
        placeholder_order = {}
        placeholder_cnt = 0
        for c in skill_content:
            if c.name is None or c.name == 'u':
                skill_desc += c.text
            elif c.name == 'font':
                ord = int(c.contents[0].attrs['data'])
                placeholder_cnt += 1
                placeholder_order[ord] = placeholder_cnt
                skill_desc += '[%s]' % placeholder_cnt
            elif c.name == 'unbreak':
                if 'data' in c.attrs:
                    ord = int(c.attrs['data'])
                    placeholder_cnt += 1
                    placeholder_order[ord] = placeholder_cnt
                    skill_desc += '[%s]' % placeholder_cnt
                else:
                    skill_desc += c.text
        cur_skill['Description' + lang] = skill_desc
        print('append skill %s desc: %s' % (lang, cur_skill['Description' + lang]))
    cur_skill['placeholder_order'] = placeholder_order # store desc placeholder order temporarily

def append_skill_attr(cur_skill, skill_dict, index):
    skill_en = skill_dict['EN']
    trs = skill_en[index].contents
    maxlevel = 0
    if trs[2].contents[0].contents[0].name == 'input':
       maxlevel = int(trs[2].contents[0].contents[0].attrs['max']) 
    buffskill = is_buff_skill(cur_skill['DescriptionEN'])
    teamskill = is_team_skill(cur_skill['DescriptionEN'])
    cur_skill['maxlevel'] = maxlevel
    cur_skill['buffskill'] = buffskill
    cur_skill['teamskill'] = teamskill
    print('append skill maxlevel: %s, buffskill: %s, teamskill: %s' % (maxlevel, buffskill, teamskill))
    
def append_skill_levelmultiplier(cur_skill, skill_dict, index):
    skill_en = skill_dict['EN']
    trs = skill_en[index].contents
    elements = trs[len(trs) - 1].contents[0].contents
    if len(elements) < 3 or 'View Details' not in elements[1].text:
        return
    # fix for non-standard html tags 
    skill_levels = elements[2].contents[0].contents[0].contents[0].contents
    placeholder_order = cur_skill['placeholder_order']
    placeholder_cnt = len(cur_skill['placeholder_order'])
    if skill_levels is None or len(skill_levels) <= placeholder_cnt + 1 or placeholder_cnt == 0:
        return
    skill_levels = skill_levels[placeholder_cnt + 1:]
    levelmultiplier = []
    for i in range(0, placeholder_cnt):
        levelmultiplier.append({})
    add_percent_sign = {}
    for i in range(0, len(skill_levels)):
        tds = skill_levels[i].contents
        if len(tds) < placeholder_cnt + 1:
            continue
        for j in range(1, 1 + placeholder_cnt):
            multiplier = tds[j].text
            if multiplier.endswith('%'):
                multiplier = multiplier.replace('%', '')
                add_percent_sign[str(placeholder_order[j - 1])] = True
            if '.' in multiplier:
                multiplier = float(multiplier)
            else:
                multiplier = int(multiplier)
            levelmultiplier[placeholder_order[j - 1] - 1][tds[0].text] = multiplier
    cur_skill['levelmultiplier'] = levelmultiplier
    print('append skill levelmultiplier, count: %s' % len(levelmultiplier))
    for k in add_percent_sign:
        for lang in languages:
            desc = cur_skill['Description' + lang]
            cur_skill['Description' + lang] = desc.replace('[%s]' % k, '[%s]%%' % k)

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
        skill_dict[lang] = soup_dict[lang].select('#char_skills > table.genshin_table.skill_table')
    skill_cnt = len(list(skill_dict['EN']))
    for i in range(0, skill_cnt):
        cur_skill = {}
        append_skill_name(cur_skill, skill_dict, i)
        append_skill_desc(cur_skill, skill_dict, i)
        append_skill_attr(cur_skill, skill_dict, i)
        append_skill_levelmultiplier(cur_skill, skill_dict, i)
        append_skill_tags(cur_skill, skill_dict, i)
        append_skill_effect(cur_skill, skill_dict, i)
        del cur_skill['placeholder_order']
        skilldata.append(cur_skill)
    result['skilldata'] = skilldata
'''
skill end
'''

# main function
def genrate_json(lightcone):
    print('generate lib json from honeyhunterworld for: %s' % lightcone)
    soup_dict = {}
    for lang in languages:
        url = 'https://hsr.honeyhunterworld.com/%s-item/?lang=%s' % (lightcone, lang)
        res = requests.get(url, headers={'User-Agent': ua.random}, timeout=10)
        soup_dict[lang] = BeautifulSoup(res.text, 'html.parser')
        if soup_dict[lang] is None or soup_dict[lang].select_one('h2.wp-block-post-title') is None:
            print('fetch failed, please try again')
            exit(1)
    with open(base_dir + '/lib/lightconelist.json', 'r', encoding='utf-8') as f:
        lightcone_info = json.load(f)
        result['id'] = list(filter(lambda i: i['ENname'].lower().replace(' ', '-') == lightcone, lightcone_info['data']))[0]['id']
    append_name(soup_dict)
    append_image(lightcone, result['id'])
    append_image_large(lightcone, result['id'])
    append_basic(soup_dict)
    append_level(soup_dict)
    append_skill(soup_dict)
    with open(base_dir + '/lib/lightcones/' + result['id'] + '.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(result, ensure_ascii=False, skipkeys=True, indent=4))


if __name__ == '__main__':
    genrate_json(sys.argv[1])
