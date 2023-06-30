# coding: utf-8

import json
import os
import re
import requests
import sys

from bs4 import BeautifulSoup
from fake_useragent import UserAgent

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # absolute path of repo dir
srs_assets_url = 'https://starrailstation.com/assets'
languages = ['EN', 'CN', 'JP']
name_lang_mapping = {'EN': 'ENname', 'CN': 'CNname', 'JP': 'JAname'} # why does it start with JA for JP localization?
stype_mapping = {'ultimate': 'ult', 'basicatk': 'basicattack'}
ua = UserAgent() # required for non-browser http request, or you will get a response code of 403
result = {}

def append_name(data_dict):
    for lang in languages:
        result[name_lang_mapping[lang]] = data_dict[lang]['name']

def append_image(character, data):
    path = 'images/characters/%s' % character
    path = download_image(path, data['splashIconPath'], 'webp')
    result['imageurl'] = path
    path = 'images/characters/%slarge' % character
    path = download_image(path, data['artPath'], 'webp')
    result['imagelargeurl'] = path

def append_basic(data):
    result['etype'] = data['damageType']['name'].lower()
    result['wtype'] = data['baseType']['name'].lower()
    result['rarity'] = str(data['rarity'])

def append_level(data):
    levels = data['levelData']
    result['dtaunt'] = levels[0]['aggro']
    result['dspeed'] = levels[0]['speedBase']
    result['maxenergy'] = data['spRequirement']
    leveldata = []
    for i in range(0, len(levels)):
        lvl = levels[i]
        lvl_incr = lvl['maxLevel'] - 1
        if i == 0:
            leveldata.append({
                'level': "1",
                'hp': lvl['hpBase'],
                'atk': lvl['attackBase'],
                'def': lvl['defenseBase'],
            })
        leveldata.append({
            'level': str(lvl['maxLevel']),
            'hp': float(round(lvl['hpBase'] + lvl['hpAdd'] * lvl_incr, 2)),
            'atk': float(round(lvl['attackBase'] + lvl['attackAdd'] * lvl_incr, 2)),
            'def': float(round(lvl['defenseBase'] + lvl['defenseAdd'] * lvl_incr, 2)),
        })
        if i < len(levels) - 1:
            next_lvl = levels[i + 1]
            leveldata.append({
                'level': str(lvl['maxLevel']) + '+',
                'hp': float(round(next_lvl['hpBase'] + lvl['hpAdd'] * lvl_incr, 2)),
                'atk': float(round(next_lvl['attackBase'] + lvl['hpAdd'] * lvl_incr, 2)),
                'def': float(round(next_lvl['defenseBase'] + lvl['hpAdd'] * lvl_incr, 2)),
            })
    result['leveldata'] = leveldata

'''
util function start
'''
def is_buff_skill(desc):
    return ' extended ' in desc \
        or ' extend ' in desc \
        or ' increases ' in desc \
        or ' increase ' in desc \
        or ' gain ' in desc \
        or re.match(r'.*\+\d+(\.\d+)?%.*', desc) is not None

def is_team_skill(desc):
    return ' all enemies' in desc

def download_skill_image(character, skill_name, skill_type, asset_id):
    name = re.sub(r'\?|!|,|\.', '', skill_name.replace(' ', '-').lower())
    dir = 'images/skills/%s' % character
    path = '%s/%s-%s.webp' % (dir, name, skill_type)
    if not os.path.exists(base_dir + '/' + dir):
        os.mkdir(base_dir + '/' + dir)
    with open(base_dir + '/' + path, 'wb') as f:
        url = '%s/%s.webp' % (srs_assets_url, asset_id)
        res = requests.get(url, headers={'User-Agent': ua.random}, timeout=30)
        f.write(res.content)
    return path

def download_image(path, asset_id, img_type):
    path = '%s.%s' % (path, img_type)
    with open(base_dir + '/' + path, 'wb') as f:
        url = '%s/%s.%s' % (srs_assets_url, asset_id, img_type)
        res = requests.get(url, headers={'User-Agent': ua.random}, timeout=30)
        f.write(res.content)
    return path

def format_percent_number(num):
    num = float(round(num * 100, 2))
    if num == int(num):
        num = int(num)
    return num

def clean_desc(desc):
    desc = re.sub(r'(<nobr>#)(\d+)(\[\w+\])(%?)(</nobr>)', r'[\2]\4', desc)
    desc = desc.replace('<br />', ' ')
    return re.sub(r'</?\w+[^>]*?>', '', desc)
'''
util function end
'''

'''
skill start
'''
def append_skill_name(cur_skill, skill_dict, index):
    for lang in languages:
        cur_skill[name_lang_mapping[lang]] = skill_dict[lang][index]['name']

def append_skill_image(character, cur_skill, skill_en, index):
    stype = skill_en[index]['typeDescHash'].lower().replace(' ', '')
    if stype in stype_mapping:
        stype = stype_mapping[stype]
    if stype == 'basicattack':
        stype = 'na'
    elif stype == 'technique':
        stype = 'tec'
    path = 'images/skills/%s%s' % (character, stype)
    path = download_image(path, skill_en[index]['iconPath'], 'webp')
    cur_skill['imageurl'] = path

def append_skill_desc(cur_skill, skill_dict, index):
    for lang in languages:
        cur_skill['Description' + lang] = clean_desc(skill_dict[lang][index]['descHash'])

def append_skill_attr(cur_skill, skill_en, index):
    stype = skill_en[index]['typeDescHash'].lower().replace(' ', '')
    cur_skill['stype'] = stype_mapping[stype] if stype in stype_mapping else stype
    if skill_en[index]['ultimateCost'] > 0:
        cur_skill['energy'] = skill_en[index]['ultimateCost']
    cur_skill['maxlevel'] = len(skill_en[index]['levelData'])
    cur_skill['buffskill'] = is_buff_skill(cur_skill['DescriptionEN'])
    cur_skill['teamskill'] = is_team_skill(cur_skill['DescriptionEN'])
    cur_skill['weaknessbreak'] = skill_en[index]['break']
    cur_skill['energyregen'] = skill_en[index]['energy']
    
def append_skill_levelmultiplier(cur_skill, skill_en, index):
    skill_levels = skill_en[index]['levelData']
    placeholder_cnt = len(skill_levels[0]['params'])
    levelmultiplier = []
    for i in range(0, placeholder_cnt):
        levelmultiplier.append({})
    for i in range(0, len(skill_levels)):
        for j in range(0, placeholder_cnt):
            multiplier = skill_levels[i]['params'][j]
            if ('[%s]%%' % (j + 1)) in cur_skill['DescriptionEN']:
                multiplier = format_percent_number(multiplier)
            levelmultiplier[j][str(i + 1)] = multiplier
    cur_skill['levelmultiplier'] = levelmultiplier

def append_skill_tags(cur_skill, skill_en, index):
    tags = []
    cur_skill['tags'] = tags

def append_skill_effect(cur_skill, skill_en, index):
    effect = []
    cur_skill['effect'] = effect

def append_skill(character, data_dict):
    skilldata = []
    skill_dict = {}
    for lang in languages:
        skill_dict[lang] = data_dict[lang]['skills']
    skill_cnt = len(list(skill_dict['EN']))
    for i in range(0, skill_cnt):
        if skill_dict['EN'][i]['typeDescHash'] == '':
            continue
        cur_skill = {}
        append_skill_name(cur_skill, skill_dict, i)
        append_skill_image(character, cur_skill, skill_dict['EN'], i)
        append_skill_desc(cur_skill, skill_dict, i)
        append_skill_attr(cur_skill, skill_dict['EN'], i)
        append_skill_levelmultiplier(cur_skill, skill_dict['EN'], i)
        append_skill_tags(cur_skill, skill_dict['EN'], i)
        append_skill_effect(cur_skill, skill_dict['EN'], i)
        skilldata.append(cur_skill)
    result['skilldata'] = skilldata
'''
skill end
'''

'''
trace start
'''
def append_trace_name_and_desc(character, cur_trace, trace_dict, index, img_cnt):
    desc_dict = {}
    asset_id = None
    for lang in languages:
        if 'tiny' not in cur_trace:
            cur_trace['tiny'] = trace_dict[lang][index]['type'] != 1
        if cur_trace['tiny'] is False:   
            name = trace_dict[lang][index]['embedBonusSkill']['name']
            desc = clean_desc(trace_dict[lang][index]['embedBonusSkill']['descHash'])
            levelData = trace_dict[lang][index]['embedBonusSkill']['levelData'][0]['params']
            for i in range(0, len(levelData)):
                multiplier = levelData[i]
                placeholder = '[%s]' % (i + 1)
                if (placeholder + '%') in desc:
                    multiplier = format_percent_number(multiplier)
                desc = desc.replace(placeholder, str(multiplier))
            asset_id = trace_dict[lang][index]['embedBonusSkill']['iconPath']
        else:
            statusList = trace_dict[lang][index]['embedBuff']['statusList']
            multiplier = format_percent_number(statusList[0]['value'])
            name = '%s +%s%%' % (statusList[0]['key'], multiplier)
            name = re.sub(r'</?\w+[^>]*?>', '', name)
            desc = ''
            if trace_dict[lang][index]['embedBuff']['levelReq'] > 0:
                desc = 'LV%s' % trace_dict[lang][index]['embedBuff']['levelReq']
            elif trace_dict[lang][index]['embedBuff']['promotionReq'] > 0:
                desc = 'A%s' % trace_dict[lang][index]['embedBuff']['promotionReq']
        cur_trace[name_lang_mapping[lang]] = name
        desc_dict['Description' + lang] = desc
    if asset_id is not None:
        path = 'images/skills/%st%s' % (character, img_cnt + 1)
        path = download_image(path, asset_id, 'webp')
        cur_trace['imageurl'] = path
    for k, v in desc_dict.items():
        cur_trace[k] = v

def append_trace_attr(cur_trace):
    if cur_trace['tiny'] == True:
        cur_trace['ttype'] = re.sub(r'^(.*?)(?:\s+(Rate|Boost))?\s+\+.*', r'\1', cur_trace['ENname']).lower().replace(' ', '')
    cur_trace['stype'] = 'trace'
    cur_trace['buffskill'] = is_buff_skill(cur_trace['ENname']) or is_buff_skill(cur_trace['DescriptionEN'])
    cur_trace['teamskill'] = is_team_skill(cur_trace['ENname']) or is_team_skill(cur_trace['DescriptionEN'])

def append_trace_tags(cur_trace, trace_dict, index):
    tags = []
    cur_trace['tags'] = tags

def append_trace_effect(cur_trace, trace_dict, index):
    effect = []
    cur_trace['effect'] = effect

def flat_trace_tree(trace_tree, trace_list):
    for t in trace_tree:
        trace_list.append(t)
        for child in t['children']:
            trace_list.append(child)

def append_trace(character, data_dict):
    tracedata = []
    trace_dict = {}
    for lang in languages:
        trace_tree = data_dict[lang]['skillTreePoints']
        trace_list = []
        flat_trace_tree(trace_tree, trace_list)
        trace_dict[lang] = trace_list
    trace_cnt = len(list(trace_dict['EN']))
    img_cnt = 0
    for i in range(0, trace_cnt):
        cur_trace = {}
        append_trace_name_and_desc(character, cur_trace, trace_dict, i, img_cnt)
        append_trace_attr(cur_trace)
        append_trace_tags(cur_trace, trace_dict, i)
        append_trace_effect(cur_trace, trace_dict, i)
        if cur_trace['tiny'] == False:
            img_cnt += 1
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
        cur_eidolon[name_lang_mapping[lang]] = eidolon_dict[lang][index]['name'].replace('<br />', ' ')

def append_eidolon_image(character, cur_eidolon, skill_en, index):
    path = 'images/skills/%s%s' % (character, index + 1)
    path = download_image(path, skill_en[index]['iconPath'], 'webp')
    cur_eidolon['imageurl'] = path

def append_eidolon_attr(cur_eidolon, eidolon_dict, index):
    for lang in languages:
        desc = clean_desc(eidolon_dict[lang][index]['descHash'])
        levelData = eidolon_dict[lang][index]['params']
        for i in range(0, len(levelData)):
            multiplier = levelData[i]
            placeholder = '[%s]' % (i + 1)
            if (placeholder + '%') in desc:
                multiplier = format_percent_number(multiplier)
            desc = desc.replace(placeholder, str(multiplier))
        cur_eidolon['Description' + lang] = desc
    cur_eidolon['stype'] = 'eidolon'
    cur_eidolon['buffskill'] = is_buff_skill(cur_eidolon['DescriptionEN'])
    cur_eidolon['teamskill'] = is_team_skill(cur_eidolon['DescriptionEN'])

def append_eidolon_tags(cur_eidolon, eidolon_dict, index):
    tags = []
    cur_eidolon['tags'] = tags

def append_eidolon_effect(cur_eidolon, eidolon_dict, index):
    effect = []
    cur_eidolon['effect'] = effect

def append_eidolon(character, data_dict):
    eidolon = []
    eidolon_dict = {}
    for lang in languages:
        eidolon_dict[lang] = data_dict[lang]['ranks']
    eidolon_cnt = len(list(eidolon_dict['EN']))
    for i in range(0, eidolon_cnt):
        cur_eidolon = {'eidolonnum': i + 1}
        append_eidolon_name(cur_eidolon, eidolon_dict, i)
        append_eidolon_image(character, cur_eidolon, eidolon_dict['EN'], i)
        append_eidolon_attr(cur_eidolon, eidolon_dict, i)
        append_eidolon_tags(cur_eidolon, eidolon_dict, i)
        append_eidolon_effect(cur_eidolon, eidolon_dict, i)
        eidolon.append(cur_eidolon)
    result['eidolon'] = eidolon
'''
eidolon end
'''

def find_data_script(tag):
    return tag.name == 'script' and 'window.PAGE_CONFIG' in tag.text

# main function
def genrate_json(lightcone):
    print('generate lib json from starrailstation for: %s' % lightcone)
    c = lightcone.replace('-', '')
    data_dict = {}
    for lang in languages:
        url = 'https://starrailstation.com/%s/character/%s' % (lang.lower(), c)
        res = requests.get(url, headers={'User-Agent': ua.random}, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')
        scripts = soup.find_all(find_data_script)
        if scripts is None or len(scripts) == 0:
            print('fetch failed, please try again')
            exit(1)
        data_script = scripts[0]
        data_json = re.sub(r',\s*window\.LANG_ID\s*=.*$', '', re.sub(r'^.*window\.PAGE_CONFIG\s*=\s*', '', data_script.text))
        data_dict[lang] = json.loads(data_json)
    # print(json.dumps(data_dict['EN'], ensure_ascii=False, skipkeys=True))
    data_dict['id'] = lightcone_id
    append_name(data_dict)
    append_image(c, data_dict['EN'])
    append_basic(data_dict['EN'])
    append_level(data_dict['EN'])
    append_skill(c, data_dict)
    append_trace(c, data_dict)
    append_eidolon(c, data_dict)
    with open(base_dir + '/lib/' + c + '.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(result, ensure_ascii=False, skipkeys=True, indent=4))


if __name__ == '__main__':
    genrate_json(sys.argv[1])
