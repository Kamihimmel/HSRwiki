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
stype_mapping = {'ultimate': 'ult', 'basicatk': 'basicattack'}
ua = UserAgent() # required for non-browser http request, or you will get a response code of 403
result = {}

def append_name(soup_dict):
    for lang in languages:
        result[name_lang_mapping[lang]] = soup_dict[lang].select_one('h2.wp-block-post-title').text
        print('append %s name: %s' % (lang, result[name_lang_mapping[lang]]))

def append_image(character):
    path = 'images/characters/%s.webp' % character
    result['imageurl'] = path
    with open(base_dir + '/' + path, 'wb') as f:
        url = 'https://hsr.honeyhunterworld.com/img/character/%s-character_cut_in_icon.webp' % character
        res = requests.get(url, headers={'User-Agent': ua.random}, timeout=30)
        f.write(res.content)
    print('append image: %s' % path)

def append_image_large(character):
    path = 'images/characters/%slarge.webp' % character
    result['imagelargeurl'] = path
    with open(base_dir + '/' + path, 'wb') as f:
        url = 'https://hsr.honeyhunterworld.com/img/character/%s-character_cut_in_front.webp' % character
        res = requests.get(url, headers={'User-Agent': ua.random}, timeout=30)
        f.write(res.content)
    print('append large image: %s' % path)

def append_basic(soup_dict):
    soup = soup_dict['EN']
    etype = None
    wtype = None
    rarity = None
    main_trs = soup.select('table.genshin_table.main_table > tr')
    for tr in main_trs:
        children = tr.contents
        if children[0].text == 'Rarity':
            rarity = str(len(children[1].contents))
        elif children[0].text == 'Path':
            wtype = children[1].text.lower().strip()
        elif children[0].text == 'Combat Types':
            etype = children[1].text.lower().strip()
    result['etype'] = etype
    result['wtype'] = wtype
    result['rarity'] = rarity
    print('append etype: %s, wtype: %s, rarity: %s' % (etype, wtype, rarity))

def append_level(soup_dict):
    soup = soup_dict['EN']
    leveldata = []
    stats_trs = soup.select('table.genshin_table.stat_table > tr')
    for tr in stats_trs:
        children = tr.contents
        if len(children) < 9:
            continue
        level = children[0].text
        if level == '80':
            result['dtaunt'] = int(children[7].text)
            result['dspeed'] = int(children[4].text)
            result['maxenergy'] = int(children[8].text)
        leveldata.append({
            'level': level,
            'hp': int(children[3].text),
            'atk': float(children[1].text) if '.' in children[1].text else int(children[1].text),
            'def': float(children[2].text) if '.' in children[2].text else int(children[2].text),
        })
    result['leveldata'] = leveldata
    print('append leveldata, count: %s' % len(leveldata))

'''
skill start
'''
def append_skill_name(cur_skill, skill_dict, index):
    full_skill_name = None
    for lang in languages:
        skill_name = skill_dict[lang][index].contents[0].contents[1].text
        cur_skill[name_lang_mapping[lang]] = skill_name.split(' - ')[0]
        if lang == 'EN':
            full_skill_name = skill_name
    print('append skill %s name: %s' % (lang, cur_skill[name_lang_mapping[lang]]))
    cur_skill['full_skill_name'] = full_skill_name # store skill tags temporarily

def append_skill_image(character, cur_skill):
    path = util.download_skill_image(character, cur_skill['ENname'], 'skill', base_dir)
    cur_skill['imageurl'] = path
    print('append skill image: %s' % path)

def append_skill_desc(cur_skill, skill_dict, index):
    for lang in languages:
        skill_content = skill_dict[lang][index].contents[3].contents[0].contents
        skill_desc = ''
        placeholder_order = {}
        placeholder_cnt = 0
        for c in skill_content:
            if c.name is None or c.name == 'u':
                skill_desc += c.text
            elif c.name == 'font':
                ord = int(c.contents[0].contents[0].attrs['data'])
                placeholder_cnt += 1
                placeholder_order[ord] = placeholder_cnt
                skill_desc += '[%s]' % placeholder_cnt
            elif c.name == 'unbreak':
                ord = int(c.contents[0].attrs['data'])
                placeholder_cnt += 1
                placeholder_order[ord] = placeholder_cnt
                skill_desc += '[%s]' % placeholder_cnt
        cur_skill['Description' + lang] = skill_desc
        print('append skill %s desc: %s' % (lang, cur_skill['Description' + lang]))
    cur_skill['placeholder_order'] = placeholder_order # store desc placeholder order temporarily

def append_skill_attr(cur_skill, skill_dict, index):
    stype = ''
    full_skill_name = cur_skill['full_skill_name']
    if ' - ' in full_skill_name:
        skill_attr = full_skill_name.split(' - ')[1]
        stype = skill_attr.split(' | ')[0].lower().replace(' ', '')
    skill_en = skill_dict['EN']
    trs = skill_en[index].contents
    maxlevel = 0
    if trs[4].contents[0].contents[0].name == 'input':
        ml = int(trs[4].contents[0].contents[0].attrs['max'])
        if ml > 1:
           maxlevel = ml
    buffskill = util.is_buff_skill(cur_skill['DescriptionEN'])
    teamskill = util.is_team_skill(cur_skill['DescriptionEN'])
    weaknessbreak = int(re.match(r'.*\S+\s+(\d+)$', trs[2].contents[0].text).group(1))
    energyregen = int(re.match(r'.*\S+\s+(\d+)$', trs[1].contents[0].text).group(1))
    cur_skill['stype'] = stype_mapping[stype] if stype in stype_mapping else stype
    cur_skill['maxlevel'] = maxlevel
    cur_skill['buffskill'] = buffskill
    cur_skill['teamskill'] = teamskill
    cur_skill['weaknessbreak'] = weaknessbreak
    cur_skill['energyregen'] = energyregen
    print('append skill stype: %s, maxlevel: %s, buffskill: %s, teamskill: %s, weaknessbreak: %s, energyregen: %s' % (stype, maxlevel, buffskill, teamskill, weaknessbreak, energyregen))
    
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
    if skill_levels is None or len(skill_levels) <= placeholder_cnt + 2 or placeholder_cnt == 0:
        return
    skill_levels = skill_levels[placeholder_cnt + 2:]
    if len(skill_levels) == 1:
        tds = skill_levels[0].contents
        for lang in languages:
            desc = cur_skill['Description' + lang] 
            for j in range(1, 1 + placeholder_cnt):
                multiplier = tds[j].text
                desc = desc.replace('[%s]' % (placeholder_order[j - 1]), tds[j].text)
            cur_skill['Description' + lang] = desc
    else:
        levelmultiplier = []
        for i in range(0, placeholder_cnt):
            levelmultiplier.append({})
        add_percent_sign = {}
        for i in range(0, len(skill_levels)):
            tds = skill_levels[i].contents
            if len(tds) < placeholder_cnt + 2:
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
    skill_en = skill_dict['EN']
    tags = []
    full_skill_name = cur_skill['full_skill_name']
    skill_attr = full_skill_name.split(' - ')[1]
    if ' | ' in skill_attr:
        tags.append(skill_attr.split(' | ')[1].lower().replace(' ', ''))
    cur_skill['tags'] = tags

def append_skill_effect(cur_skill, skill_dict, index):
    effect = []
    cur_skill['effect'] = effect

def append_skill(character, soup_dict):
    skilldata = []
    skill_dict = {}
    for lang in languages:
        skill_dict[lang] = soup_dict[lang].select('#char_skills > table.genshin_table.skill_table')
    skill_cnt = len(list(skill_dict['EN']))
    for i in range(0, skill_cnt):
        cur_skill = {}
        append_skill_name(cur_skill, skill_dict, i)
        if ' - ' not in cur_skill['full_skill_name']:
            continue
        append_skill_image(character, cur_skill)
        append_skill_desc(cur_skill, skill_dict, i)
        append_skill_attr(cur_skill, skill_dict, i)
        append_skill_levelmultiplier(cur_skill, skill_dict, i)
        append_skill_tags(cur_skill, skill_dict, i)
        append_skill_effect(cur_skill, skill_dict, i)
        del cur_skill['full_skill_name']
        del cur_skill['placeholder_order']
        skilldata.append(cur_skill)
    result['skilldata'] = skilldata
'''
skill end
'''

'''
trace start
'''
def append_trace_name_and_desc(cur_trace, trace_dict, index):
    desc = {}
    for lang in languages:
        table = trace_dict[lang][index]
        trace_name = table.contents[0].contents[1].text
        trace_desc_el = table.contents[0].contents[2]
        trace_condition_el = None
        if 'Requires Character' in trace_desc_el.text or '需要角色' in trace_desc_el.text or 'キャラクター' in trace_desc_el.text:
            # trace has pre-condition
            trace_condition_el = trace_desc_el
            trace_desc_el = table.contents[0].contents[3]
        trace_desc = ''
        for e in trace_desc_el.contents:
            trace_desc += e.text
        if 'tiny' not in cur_trace:
            cur_trace['tiny'] = re.match(r'^.*\(.*\)$', trace_name) is not None
        if cur_trace['tiny'] is True:   
            cur_trace[name_lang_mapping[lang]] = trace_desc
            if trace_condition_el is None:
                desc['Description' + lang] = 'LV1'
            else:
                if lang == 'EN':
                    prefix = ''
                    cond = re.match(r'.*\S+\s+(\d+)$', trace_condition_el.text).group(1)
                    if 'Lv.' in trace_condition_el.text:
                        prefix = 'LV'
                    elif 'Ascension' in trace_condition_el.text:
                        prefix = 'A'
                    for lang in languages:
                        desc['Description' + lang] = prefix + cond
        else:
            cur_trace[name_lang_mapping[lang]] = trace_name
            desc['Description' + lang] = trace_desc
        print('append trace %s name: %s' % (lang, trace_name))
    for k, v in desc.items():
        cur_trace[k] = v
        print('append trace %s desc: %s' % (k, v))

def append_trace_attr(character, cur_trace):
    if cur_trace['tiny'] == True:
        cur_trace['ttype'] = re.match(r'^(.*?)(?:\s+Rate)?\s+(increases|decreases).*', cur_trace['ENname']).group(1).lower().replace(' ', '')
    else:
        path = util.download_skill_image(character, cur_trace['ENname'], 'trace', base_dir)
        cur_trace['imageurl'] = path
        print('append trace image: %s' % path)
    cur_trace['stype'] = 'trace'
    cur_trace['buffskill'] = util.is_buff_skill(cur_trace['ENname'])
    cur_trace['teamskill'] = util.is_team_skill(cur_trace['ENname'])
    print('append skill stype: %s, buffskill: %s, teamskill: %s' % (cur_trace['stype'], cur_trace['buffskill'], cur_trace['teamskill']))

def append_trace_tags(cur_trace, trace_dict, index):
    tags = []
    cur_trace['tags'] = tags

def append_trace_effect(cur_trace, trace_dict, index):
    effect = []
    cur_trace['effect'] = effect

def append_trace(character, soup_dict):
    tracedata = []
    trace_dict = {}
    for lang in languages:
        trace_dict[lang] = soup_dict[lang].select('#char_trace table.genshin_table.skill_table.trace_table')
    trace_cnt = len(list(trace_dict['EN']))
    for i in range(0, trace_cnt):
        cur_trace = {}
        append_trace_name_and_desc(cur_trace, trace_dict, i)
        append_trace_attr(character, cur_trace)
        append_trace_tags(cur_trace, trace_dict, i)
        append_trace_effect(cur_trace, trace_dict, i)
        tracedata.append(cur_trace)
    result['tracedata'] = tracedata
'''
trace end
'''

'''
eidolon start
'''
def append_eidolon_name(cur_eidolon, eidolon_dict, index):
    for lang in languages:
        eidolon_name = eidolon_dict[lang][index].contents[0].contents[1].text
        cur_eidolon[name_lang_mapping[lang]] = eidolon_name
        print('append eidolon %s name: %s' % (lang, cur_eidolon[name_lang_mapping[lang]]))

def append_eidolon_image(character, cur_eidolon):
    path = util.download_skill_image(character, cur_eidolon['ENname'], 'eidolon', base_dir)
    cur_eidolon['imageurl'] = path
    print('append eidolon image: %s' % path)

def append_eidolon_attr(cur_eidolon, eidolon_dict, index):
    for lang in languages:
        eidolon_desc_el = eidolon_dict[lang][index].contents[1].contents[0]
        eidolon_desc = ''
        for e in eidolon_desc_el.contents:
            eidolon_desc += e.text
        cur_eidolon['Description' + lang] = eidolon_desc
        print('append eidolon %s desc: %s' % (lang, eidolon_desc))
    cur_eidolon['stype'] = 'eidolon'
    cur_eidolon['buffskill'] = util.is_buff_skill(cur_eidolon['DescriptionEN'])
    cur_eidolon['teamskill'] = util.is_team_skill(cur_eidolon['DescriptionEN'])
    print('append eidolon stype: %s, buffskill: %s, teamskill: %s' % (cur_eidolon['stype'], cur_eidolon['buffskill'], cur_eidolon['teamskill']))

def append_eidolon_tags(cur_eidolon, eidolon_dict, index):
    tags = []
    cur_eidolon['tags'] = tags

def append_eidolon_effect(cur_eidolon, eidolon_dict, index):
    effect = []
    cur_eidolon['effect'] = effect

def append_eidolon(character, soup_dict):
    eidolon = []
    eidolon_dict = {}
    for lang in languages:
        eidolon_dict[lang] = soup_dict[lang].select('#char_eidolon table.genshin_table.skill_table')
    eidolon_cnt = len(list(eidolon_dict['EN']))
    for i in range(0, eidolon_cnt):
        cur_eidolon = {'eidolonnum': i + 1}
        append_eidolon_name(cur_eidolon, eidolon_dict, i)
        append_eidolon_image(character, cur_eidolon)
        append_eidolon_attr(cur_eidolon, eidolon_dict, i)
        append_eidolon_tags(cur_eidolon, eidolon_dict, i)
        append_eidolon_effect(cur_eidolon, eidolon_dict, i)
        eidolon.append(cur_eidolon)
    result['eidolon'] = eidolon
'''
eidolon end
'''

# main function
def genrate_json(character):
    print('generate lib json from honeyhunterworld for: %s' % character)
    soup_dict = {}
    for lang in languages:
        url = 'https://hsr.honeyhunterworld.com/%s-character/?lang=%s' % (character, lang)
        res = requests.get(url, headers={'User-Agent': ua.random}, timeout=10)
        soup_dict[lang] = BeautifulSoup(res.text, 'html.parser')
        if soup_dict[lang] is None or soup_dict[lang].select_one('h2.wp-block-post-title') is None:
            print('fetch failed, please try again')
            exit(1)
    append_name(soup_dict)
    append_image(character.replace('-', ''))
    append_image_large(character.replace('-', ''))
    append_basic(soup_dict)
    append_level(soup_dict)
    append_skill(character, soup_dict)
    append_trace(character, soup_dict)
    append_eidolon(character, soup_dict)
    with open(base_dir + '/lib/' + character.replace('-', '') + '.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(result, ensure_ascii=False, skipkeys=True, indent=4))


if __name__ == '__main__':
    genrate_json(sys.argv[1])
