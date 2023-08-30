# coding: utf-8

import json
import os
import re
import requests
import sys

import util

from fake_useragent import UserAgent

from crawler.relic_yatta import part_mapping

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # absolute path of repo dir
languages = ['en', 'cn', 'jp']
name_lang_mapping = {'en': 'ENname', 'cn': 'CNname', 'jp': 'JAname'}
ua = UserAgent()  # required for non-browser http request, or you will get a response code of 403
util.prepare_dirs('yatta', base_dir)

data_dict = {}
for lang in languages:
    url = 'https://api.yatta.top/hsr/v2/%s/relic' % lang
    res = requests.get(url, headers={'User-Agent': ua.edge}, timeout=30)
    print('response: %s' % res.content)
    data = json.loads(res.content)
    if data is None or data['response'] != 200:
        print('fetch failed, please try again')
        sys.exit(1)
    data_dict[lang] = data['data']['items']

with open(base_dir + '/lib/reliclist.json', 'r', encoding='utf-8') as f:
    exist_list = json.load(f)['data']

characters = []
exist_ids = []
for c in exist_list:
    characters.append(c)
    exist_ids.append(c['id'])

for k in data_dict['en']:
    if k in exist_ids:
        continue
    result = {}
    result['id'] = k
    data_en = data_dict['en']
    for lang in languages:
        result[name_lang_mapping[lang]] = data_dict[lang][k]['name']
    img_ext = 'png'
    path = 'images/relics/%s' % k
    util.download_yatta_image('crawler/yatta/' + path, 'relic', data_en[k]['icon'], img_ext, base_dir)
    result['imageurl'] = '%s.%s' % (path, img_ext)
    result['set'] = '2' if data_en[k]['isPlanarSuit'] else '4'
    url = 'https://api.yatta.top/hsr/v2/en/relic/%s' % result['id']
    res = requests.get(url, headers={'User-Agent': ua.edge}, timeout=(10, 30))
    relic_data = json.loads(res.content)
    if relic_data and 'response' in relic_data and relic_data['response'] == 200:
        suite = relic_data['data']['suite']
        for suiteKey, suiteValue in suite.items():
            p = suiteKey.lower()
            part = part_mapping[p] if p in part_mapping else p
            icon = suiteValue['icon']
            img_ext = 'png'
            path = 'images/relics/%s' % icon
            util.download_yatta_image('crawler/yatta/' + path, 'relic', icon, img_ext, base_dir)
            result[re.sub(r'^.*?\s+', '', part)] = '%s.%s' % (path, img_ext)
    result['infourl'] = 'lib/relics/%s.json' % k
    result['spoiler'] = data_en[k]['beta'] if 'beta' in data_en[k] else False
    if result['spoiler']:
        result['ENname'] += '(WIP)'
        result['CNname'] += '(施工中)'
        result['JAname'] += '(建設中)'
    print("fetch data for: %s" % result['ENname'])
    characters.append(result)

with open(base_dir + '/crawler/yatta/lib/reliclist.json', 'w', encoding='utf-8') as f:
    f.write(json.dumps({'data': characters}, ensure_ascii=False, skipkeys=True, indent=4))
