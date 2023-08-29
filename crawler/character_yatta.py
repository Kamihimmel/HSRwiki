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
stype_mapping = {'ultimate': 'ult', 'basicatk': 'basicattack'}
ttype_mapping = {'maxhp': 'hp', 'effecthitrate': 'effecthit'}
ua = UserAgent()  # required for non-browser http request, or you will get a response code of 403
result = {}


def append_name(data_dict):
    for lang in languages:
        result[name_lang_mapping[lang]] = data_dict[lang]['name']
        print('append %s name: %s' % (lang, result[name_lang_mapping[lang]]))


def append_image(character_id, size):
    img_ext = 'png'
    path = 'images/characters/%s%s' % (character_id, '-large' if size == 'large' else '')
    util.download_yatta_image('crawler/yatta/' + path, 'avatar', size + '/' + character_id, img_ext, base_dir)
    result['imagelargeurl' if size == 'large' else 'imageurl'] = '%s.%s' % (path, img_ext)
    print('append image: %s' % path)


def append_basic(data_dict):
    data_en = data_dict['EN']
    result['etype'] = data_en['types']['combatType']['name'].lower().replace(' ', '')
    result['wtype'] = data_en['types']['pathType']['name'].lower().replace(' ', '')
    result['rarity'] = str(data_en['rank'])
    print('append etype: %s, wtype: %s, rarity: %s' % (result['etype'], result['wtype'], result['rarity']))


def append_level(data_dict):
    upgrade = data_dict['EN']['upgrade']
    last_upgrade = upgrade[len(upgrade) - 1]
    result['dtaunt'] = last_upgrade['skillBase']['baseAggro']
    result['dspeed'] = last_upgrade['skillBase']['speedBase']
    maxenergy = 0
    skills = data_dict['EN']['traces']['mainSkills']
    for k, v in skills.items():
        for s in v['skillList'].values():
            if s['type'] == 'Ultimate':
                maxenergy = s['skillPoints']['need']
                break
        if maxenergy > 0:
            break
    result['maxenergy'] = maxenergy
    print('append dtaunt: %s, dspeed: %s, maxenergy: %s' % (result['dtaunt'], result['dspeed'], result['maxenergy']))
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
    print('append leveldata, count: %s' % len(leveldata))


'''
skill start
'''


def append_skill_name(cur_skill, skill_dict, index):
    for lang in languages:
        cur_skill[name_lang_mapping[lang]] = skill_dict[lang][index]['name']
        print('append skill %s name: %s' % (lang, cur_skill[name_lang_mapping[lang]]))


def append_skill_image(character_id, cur_skill, skill_dict, index):
    img_ext = 'png'
    path = 'images/skills/%s-%s' % (character_id, cur_skill['id'])
    util.download_yatta_image('crawler/yatta/' + path, 'skill', skill_dict['EN'][index]['icon'], img_ext, base_dir)
    cur_skill['imageurl'] = '%s.%s' % (path, img_ext)
    print('append skill image: %s' % path)


def append_skill_desc(cur_skill, skill_dict, index):
    for lang in languages:
        desc = cur_skill['Description' + lang] = util.clean_desc_yatta(skill_dict[lang][index]['description'])
        if skill_dict[lang][index]['maxLevel'] <= 1 and skill_dict[lang][index]['params']:
            for k, v in skill_dict[lang][index]['params'].items():
                desc = desc.replace('[%s]' % k, str(util.format_percent_number(v[0]) if '[%s]%%' % k in desc else v[0]))
        cur_skill['Description' + lang] = desc
        print('append skill %s desc: %s' % (lang, cur_skill['Description' + lang]))


def append_skill_attr(cur_skill, skill_dict, index):
    skill_en = skill_dict['EN'][index]
    stype = skill_en['type'].replace(' ', '').lower()
    maxlevel = skill_en['maxLevel']
    if maxlevel <= 1:
        maxlevel = 0
    buffskill = util.is_buff_skill(cur_skill['DescriptionEN'])
    teamskill = util.is_team_skill(cur_skill['DescriptionEN'])
    weaknessbreak = skill_en['weaknessBreak']['one'] if skill_en['weaknessBreak'] is not None \
                                                        and 'one' in skill_en['weaknessBreak'] and \
                                                        skill_en['weaknessBreak']['one'] is not None else 0
    if weaknessbreak == 0:
        weaknessbreak = skill_en['weaknessBreak']['all'] if skill_en['weaknessBreak'] is not None \
                                                            and 'all' in skill_en['weaknessBreak'] and \
                                                            skill_en['weaknessBreak']['all'] is not None else 0
    energyregen = skill_en['skillPoints']['base'] if skill_en['skillPoints'] is not None \
                                                     and 'base' in skill_en['skillPoints'] and skill_en['skillPoints'][
                                                         'base'] is not None else 0
    energyneed = skill_en['skillPoints']['need'] if skill_en['skillPoints'] is not None \
                                                    and 'need' in skill_en['skillPoints'] and skill_en['skillPoints'][
                                                        'need'] is not None else 0
    cur_skill['stype'] = stype_mapping[stype] if stype in stype_mapping else stype
    if energyneed > 0:
        cur_skill['energy'] = energyneed
        print('append skill energy need: %s' % energyneed)
    cur_skill['maxlevel'] = maxlevel
    cur_skill['buffskill'] = buffskill
    cur_skill['teamskill'] = teamskill
    cur_skill['weaknessbreak'] = weaknessbreak
    cur_skill['energyregen'] = energyregen
    print('append skill stype: %s, maxlevel: %s, buffskill: %s, teamskill: %s, weaknessbreak: %s, energyregen: %s' % (
        stype, maxlevel, buffskill, teamskill, weaknessbreak, energyregen))


def append_skill_levelmultiplier(cur_skill, skill_dict, index):
    if cur_skill['maxlevel'] == 0:
        return
    skill_en = skill_dict['EN'][index]
    desc = cur_skill['DescriptionEN']
    params = skill_en['params']
    levelmultiplier = []
    for i, multi in params.items():
        percent = ('[%s]%%' % i) in desc
        d = {}
        for j in range(0, len(multi)):
            d[str(j + 1)] = util.format_percent_number(multi[j]) if percent else multi[j]
        levelmultiplier.append(d)
    cur_skill['levelmultiplier'] = levelmultiplier
    print('append skill levelmultiplier, count: %s' % len(levelmultiplier))


def append_skill_tags(cur_skill, exist_skill):
    if 'tags' in exist_skill and len(exist_skill['tags']) > 0:
        cur_skill['tags'] = exist_skill['tags']


def append_skill_effect(cur_skill, exist_skill):
    if 'effect' in exist_skill and len(exist_skill['effect']) > 0:
        cur_skill['effect'] = exist_skill['effect']


def compare_skill(s, d):
    if 'id' in s and 'id' in d:
        return s['id'] == d['id']
    return s['ENname'] == d['ENname']


def append_skill(character_id, data_dict, exist_dict):
    skilldata = []
    skill_dict = {}
    for lang in languages:
        main_skills = data_dict[lang]['traces']['mainSkills']
        skills = []
        for ms in main_skills.values():
            for k, v in ms['skillList'].items():
                v['id'] = k
                skills.append(v)
        skill_dict[lang] = skills
    exist_skills = exist_dict['skilldata'] if 'skilldata' in exist_dict else {}
    for i in range(0, len(skill_dict['EN'])):
        cur_skill = {'id': skill_dict['EN'][i]['id']}
        append_skill_name(cur_skill, skill_dict, i)
        append_skill_image(character_id, cur_skill, skill_dict, i)
        append_skill_desc(cur_skill, skill_dict, i)
        append_skill_attr(cur_skill, skill_dict, i)
        append_skill_levelmultiplier(cur_skill, skill_dict, i)
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

'''
trace start
'''


def append_trace_name_and_desc(cur_trace, trace_dict, index):
    trace_desc = {}
    for lang in languages:
        trace = trace_dict[lang][index]
        if cur_trace['tiny']:
            name = util.clean_desc_yatta(trace['statusList'][0]['name'])
            multiplier = trace['statusList'][0]['value']
            name = name.replace('[1]', str(util.format_percent_number(multiplier) if '[1]%' in name else multiplier))
            desc = ''
            if 'avatarLevelLimit' in trace and trace['avatarLevelLimit'] is not None:
                desc = 'LV%s' % trace['avatarLevelLimit']
            elif 'avatarPromotionLimit' in trace and trace['avatarPromotionLimit'] is not None:
                desc = 'A%s' % trace['avatarPromotionLimit']
        else:
            name = trace['name']
            desc = util.clean_desc_yatta(trace['description'])
            if 'params' in trace and trace['params'] is not None:
                for k, v in trace['params'].items():
                    desc = desc.replace('[%s]' % k,
                                        str(util.format_percent_number(v[0]) if '[%s]%%' % k in desc else v[0]))
        cur_trace[name_lang_mapping[lang]] = name
        print('append trace %s name: %s' % (lang, name))
        trace_desc['Description' + lang] = desc
    for k, v in trace_desc.items():
        cur_trace[k] = v
        print('append trace %s desc: %s' % (k, v))


def append_trace_attr(character_id, cur_trace, trace_dict, index):
    if cur_trace['tiny']:
        ttype = re.match(r'^(.*?)\s+(increases|decreases).*', cur_trace['ENname']).group(1).lower().replace(' ', '')
        cur_trace['ttype'] = ttype_mapping[ttype] if ttype in ttype_mapping else ttype
        print('append trace ttype: %s' % cur_trace['ttype'])
    else:
        img_ext = 'png'
        path = 'images/skills/%s-%s' % (character_id, cur_trace['id'])
        util.download_yatta_image('crawler/yatta/' + path, 'skill', trace_dict['EN'][index]['icon'], img_ext, base_dir)
        cur_trace['imageurl'] = '%s.%s' % (path, img_ext)
        print('append trace image: %s' % path)
    cur_trace['stype'] = 'trace'
    cur_trace['buffskill'] = util.is_buff_skill(cur_trace['ENname'])
    cur_trace['teamskill'] = util.is_team_skill(cur_trace['ENname'])
    print('append skill stype: %s, buffskill: %s, teamskill: %s' % (
        cur_trace['stype'], cur_trace['buffskill'], cur_trace['teamskill']))


def append_trace_tags(cur_trace, exist_trace):
    if 'tags' in exist_trace and len(exist_trace['tags']) > 0:
        cur_trace['tags'] = exist_trace['tags']


def append_trace_effect(cur_trace, exist_trace):
    if 'effect' in exist_trace and len(exist_trace['effect']) > 0:
        cur_trace['effect'] = exist_trace['effect']


def compare_trace(s, d):
    if 'id' in s and 'id' in d:
        return s['id'] == d['id']
    if s['ENname'] == d['ENname']:
        return True
    if 'ttype' in s and 'ttype' in d and s['ttype']:
        return s['ttype'] == d['ttype'] and s['DescriptionEN'] == d['DescriptionEN']
    return False


def append_trace(character_id, data_dict, exist_dict):
    tracedata = []
    trace_dict = {}
    for lang in languages:
        sub_skills = data_dict[lang]['traces']['subSkills']
        skills = []
        for ss in sub_skills.values():
            skills.append(ss)
        trace_dict[lang] = skills
    exist_traces = exist_dict['tracedata'] if 'tracedata' in exist_dict else {}
    trace_cnt = len(list(trace_dict['EN']))
    for i in range(0, trace_cnt):
        cur_trace = {'id': str(trace_dict['EN'][i]['id']), 'tiny': not trace_dict['EN'][i]['pointType'] == 'Special'}
        append_trace_name_and_desc(cur_trace, trace_dict, i)
        append_trace_attr(character_id, cur_trace, trace_dict, i)
        find = list(filter(lambda s: compare_trace(s, cur_trace), exist_traces))
        exist_trace = find[0] if len(find) > 0 else {}
        append_trace_tags(cur_trace, exist_trace)
        append_trace_effect(cur_trace, exist_trace)
        tracedata.append(cur_trace)
    result['tracedata'] = tracedata
    print('append tracedata, count: %s' % len(tracedata))


'''
trace end
'''

'''
eidolon start
'''


def append_eidolon_name(cur_eidolon, eidolon_dict, index):
    for lang in languages:
        cur_eidolon[name_lang_mapping[lang]] = eidolon_dict[lang][index]['name'].replace('\\n', ' ')
        print('append eidolon %s name: %s' % (lang, cur_eidolon[name_lang_mapping[lang]]))


def append_eidolon_image(character_id, cur_eidolon, eidolon_dict, index):
    img_ext = 'png'
    path = 'images/skills/%s-e%s' % (character_id, cur_eidolon['eidolonnum'])
    util.download_yatta_image('crawler/yatta/' + path, 'skill', eidolon_dict['EN'][index]['icon'], img_ext, base_dir)
    cur_eidolon['imageurl'] = '%s.%s' % (path, img_ext)
    print('append eidolon image: %s' % path)


def append_eidolon_attr(cur_eidolon, eidolon_dict, index):
    for lang in languages:
        desc = util.clean_desc_yatta(eidolon_dict[lang][index]['description'])
        params = eidolon_dict[lang][index]['params']
        if params is not None:
            for i in range(0, len(params)):
                desc = desc.replace('[%s]' % (i + 1),
                                    str(util.format_percent_number(params[i]) if '[%s]%%' % (i + 1) in desc else params[
                                        i]))
        cur_eidolon['Description' + lang] = desc
        print('append eidolon %s desc: %s' % (lang, desc))
    cur_eidolon['stype'] = 'eidolon'
    cur_eidolon['buffskill'] = util.is_buff_skill(cur_eidolon['DescriptionEN'])
    cur_eidolon['teamskill'] = util.is_team_skill(cur_eidolon['DescriptionEN'])
    print('append eidolon stype: %s, buffskill: %s, teamskill: %s' % (
        cur_eidolon['stype'], cur_eidolon['buffskill'], cur_eidolon['teamskill']))


def append_eidolon_tags(cur_eidolon, exist_eidolon):
    if 'tags' in exist_eidolon and len(exist_eidolon['tags']) > 0:
        cur_eidolon['tags'] = exist_eidolon['tags']


def append_eidolon_effect(cur_eidolon, exist_eidolon):
    if 'effect' in exist_eidolon and len(exist_eidolon['effect']) > 0:
        cur_eidolon['effect'] = exist_eidolon['effect']


def compare_eidolon(s, d):
    if 'id' in s and 'id' in d:
        return s['id'] == d['id']
    return s['eidolonnum'] == d['eidolonnum']


def append_eidolon(character_id, data_dict, exist_dict):
    eidolon = []
    eidolon_dict = {}
    for lang in languages:
        eidolons = []
        for v in data_dict[lang]['eidolons'].values():
            eidolons.append(v)
        eidolon_dict[lang] = eidolons
    exist_eidolons = exist_dict['eidolon'] if 'eidolon' in exist_dict else {}
    eidolon_cnt = len(list(eidolon_dict['EN']))
    for i in range(0, eidolon_cnt):
        cur_eidolon = {'id': str(eidolon_dict['EN'][i]['id']), 'eidolonnum': eidolon_dict['EN'][i]['rank']}
        append_eidolon_name(cur_eidolon, eidolon_dict, i)
        append_eidolon_image(character_id, cur_eidolon, eidolon_dict, i)
        append_eidolon_attr(cur_eidolon, eidolon_dict, i)
        find = list(filter(lambda s: compare_eidolon(s, cur_eidolon), exist_eidolons))
        exist_eidolon = find[0] if len(find) > 0 else {}
        append_eidolon_tags(cur_eidolon, exist_eidolon)
        append_eidolon_effect(cur_eidolon, exist_eidolon)
        eidolon.append(cur_eidolon)
    result['eidolon'] = eidolon
    print('append eidolon, count: %s' % len(eidolon))


'''
eidolon end
'''


# main function
def generate_json(character_id):
    util.prepare_dirs('yatta', base_dir)
    result['id'] = character_id
    exist_list = base_dir + '/crawler/yatta/lib/characterlist.json'
    if not os.path.exists(exist_list):
        exist_list = base_dir + '/lib/characterlist.json'
    with open(exist_list, 'r', encoding='utf-8') as f:
        character_info = json.load(f)
        character = list(filter(lambda i: i['id'] == character_id, character_info['data']))[0]
    print('generate lib json from yatta for: %s %s' % (character_id, character['ENname']))
    exist_dict = {}
    exist_path = base_dir + '/' + character['infourl']
    if os.path.exists(exist_path):
        with open(exist_path, 'r', encoding='utf-8') as f:
            exist_dict = json.load(f)
    data_dict = {}
    for lang in languages:
        url = 'https://api.yatta.top/hsr/v2/%s/avatar/%s' % (lang, result['id'])
        res = requests.get(url, headers={'User-Agent': ua.edge}, timeout=(10, 30))
        print('response: %s' % res.content)
        data = json.loads(res.content)
        if data is None or 'response' not in data or data['response'] != 200:
            print('fetch failed, please try again')
            exit(1)
        data_dict[lang] = data['data']
    append_name(data_dict)
    append_image(character_id, 'medium')
    append_image(character_id, 'large')
    append_basic(data_dict)
    append_level(data_dict)
    append_skill(character_id, data_dict, exist_dict)
    append_trace(character_id, data_dict, exist_dict)
    append_eidolon(character_id, data_dict, exist_dict)
    with open(base_dir + '/crawler/yatta/lib/characters/' + result['id'] + '.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(result, ensure_ascii=False, skipkeys=True, indent=4))


if __name__ == '__main__':
    generate_json(sys.argv[1])
