# coding: utf-8

import json
import os
import re

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # absolute path of repo dir
languages = ['EN', 'CN', 'JP']
name_lang_mapping = {'EN': 'ENname', 'CN': 'CNname', 'JP': 'JAname'}
enemy_category = ['antimatter-legion', 'jarilo-vi', 'the-xianzhou-luofu', 'fragmentum-monsters', 'simulated-universe', 'stellaron-hunters', 'cosmos', 'other']
etype_mapping = {'Minion': 'minion', 'Enemy Creatures': 'normal', 'Elite Enemy': 'elite', 'Boss Enemy': 'boss'}
ua = UserAgent()  # required for non-browser http request, or you will get a response code of 403
result = []
skip_image = True


# main function
def append_name(enemy, hoyolab_data, data_dict, index):
    for lang in languages:
        soup = BeautifulSoup(data_dict[lang][index][1], 'html.parser')
        name = soup.select_one('a').text
        if lang == 'EN':
            find = list(filter(lambda e: e['name'] == name, hoyolab_data.values()))
            if len(find) > 0:
                enemy['id'] = find[0]['entry_page_id']
                print('append id: %s' % enemy['id'])
        enemy[name_lang_mapping[lang]] = name
        print('append %s name: %s' % (lang, enemy[name_lang_mapping[lang]]))


def append_category(enemy, category_dict):
    enemy['category'] = category_dict['EN']
    print('append category: %s' % enemy['category'])


def append_image(enemy):
    headers = {
        'Authority': 'sg-wiki-api-static.hoyolab.com',
        'User-Agent': ua.random,
        'Referer': 'https://wiki.hoyolab.com/',
        'X-Rpc-Language': 'en-us',
        'X-Rpc-Wiki_app': 'hsr',
    }
    res = requests.get('https://sg-wiki-api-static.hoyolab.com/hoyowiki/hsr/wapi/entry_page?entry_page_id=%s' % enemy['id'], headers=headers, timeout=10)
    details_res = json.loads(res.content)
    icon_url = details_res['data']['page']['icon_url']
    if icon_url != '':
        ext = icon_url[icon_url.rfind('.') + 1:]
        path = 'images/enemies/%s.%s' % (enemy['id'], ext)
        enemy['imageurl'] = path
        if not skip_image:
            with open(base_dir + '/' + path, 'wb') as f:
                res = requests.get(icon_url, headers={'User-Agent': ua.random}, timeout=30)
                f.write(res.content)
    else:
        enemy['imageurl'] = ''
    print('append image: %s' % enemy['imageurl'])
    header_img_url = details_res['data']['page']['header_img_url']
    if header_img_url != '':
        ext = header_img_url[header_img_url.rfind('.') + 1:]
        path = 'images/enemies/%s-large.%s' % (enemy['id'], ext)
        enemy['imagelargeurl'] = path
        if not skip_image:
            with open(base_dir + '/' + path, 'wb') as f:
                res = requests.get(header_img_url, headers={'User-Agent': ua.random}, timeout=30)
                f.write(res.content)
    else:
        enemy['imagelargeurl'] = enemy['imageurl']
    print('append large image: %s' % enemy['imagelargeurl'])


def append_basic(enemy, en_dict, index):
    enemy['etype'] = etype_mapping[en_dict[index][2]]
    print('append etype: %s' % enemy['etype'])
    soup = BeautifulSoup(en_dict[index][1], 'html.parser')
    path = soup.select_one('a').attrs['href']
    res = requests.get('https://hsr.honeyhunterworld.com' + path, headers={'User-Agent': ua.random}, timeout=10)
    soup = BeautifulSoup(res.text, 'html.parser')
    table = soup.select_one('div.tab-panels-2 > section').select('div.scroll_wrap > table.mon_variant_table')[1]
    trs = table.contents[0].contents
    weakness = []
    for img in trs[1].select_one('td').select('img'):
        src = img.attrs['src'].split('/')[3]
        weakness.append(src[0:src.find('-')])
    enemy['weakness'] = weakness
    print('append weakness: %s' % weakness)
    resistence = {}
    for tr in trs[3].select_one('td').select('tr'):
        el = tr.contents[0].select_one('a').attrs['href'].split('/')[1]
        el = el[0:el.find('-')]
        resistence[el] = int(tr.contents[1].text.replace('%', ''))
    enemy['resistence'] = resistence
    print('append resistence: %s' % resistence)


def add_enemies(soup_dict, hoyolab_data):
    category_dict = {}
    data_dict = {}
    for lang in languages:
        category_dict[lang] = soup_dict[lang].select_one('h2.wp-block-post-title').text
        script_content = soup_dict[lang].select_one('div.entry-content table.sortable > tbody > script').text
        script_content = re.compile('.*\\[\\[').sub('[[', script_content)
        script_content = re.compile(']].*').sub(']]', script_content)
        data_dict[lang] = json.loads(script_content)
    cnt = len(data_dict['EN'])
    for index in range(0, cnt):
        enemy = {}
        append_name(enemy, hoyolab_data, data_dict, index)
        if 'id' not in enemy:
            continue
        if len(list(filter(lambda e: e['id'] == enemy['id'], result))) > 0:
            continue
        append_category(enemy, category_dict)
        append_image(enemy)
        append_basic(enemy, data_dict['EN'], index)
        result.append(enemy)


def fetch_hoyolab_data():
    hoyolab_data = {}
    page = 1
    page_size = 30
    hoyolab_url = 'https://sg-wiki-api.hoyolab.com/hoyowiki/hsr/wapi/get_entry_page_list'
    headers = {
        'Authority': 'sg-wiki-api-static.hoyolab.com',
        'User-Agent': ua.random,
        'Referer': 'https://wiki.hoyolab.com/',
        'X-Rpc-Language': 'en-us',
        'X-Rpc-Wiki_app': 'hsr',
    }
    while True:
        body = {"filters": [], "menu_id": "112", "page_num": page, "page_size": page_size, "use_es": True}
        res = requests.post(hoyolab_url, data=json.dumps(body), headers=headers, timeout=10)
        hoyolab_res = json.loads(res.content)
        print('fetch hoyolab enemies, page: %s' % page)
        for e in hoyolab_res['data']['list']:
            hoyolab_data[e['entry_page_id']] = e
        total = int(hoyolab_res['data']['total'])
        if page * page_size >= total:
            break
        page += 1
    print('fetch hoyolab enemies, total: %s' % len(hoyolab_data))
    return hoyolab_data


def generate_json():
    print('generate lib json from honeyhunterworld for enemies')
    hoyolab_data = fetch_hoyolab_data()
    for category in enemy_category:
        soup_dict = {}
        for lang in languages:
            url = 'https://hsr.honeyhunterworld.com/%s-monster_faction/?lang=%s' % (category, lang)
            res = requests.get(url, headers={'User-Agent': ua.random}, timeout=10)
            soup_dict[lang] = BeautifulSoup(res.text, 'html.parser')
            if soup_dict[lang] is None or soup_dict[lang].select_one('h2.wp-block-post-title') is None:
                print('fetch failed, please try again')
                exit(1)
        add_enemies(soup_dict, hoyolab_data)
    with open(base_dir + '/lib/enemylist.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps({'data': result}, ensure_ascii=False, skipkeys=True, indent=4))


if __name__ == '__main__':
    generate_json()
