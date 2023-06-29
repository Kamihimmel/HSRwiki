# coding: utf-8

import os
import re
import requests

from fake_useragent import UserAgent

srs_assets_url = 'https://starrailstation.com/assets'
ua = UserAgent()

def is_buff_skill(desc):
    lower_desc = desc.lower()
    return 'extended' in lower_desc \
        or 'extend' in lower_desc \
        or 'increases' in lower_desc \
        or 'increase' in lower_desc \
        or 'gain' in lower_desc \
        or re.match(r'.*\+\d+(\.\d+)?%.*', desc) is not None

def is_team_skill(desc):
    lower_desc = desc.lower()
    return 'all enemies' in lower_desc

def format_percent_number(num):
    num = float(round(num * 100, 2))
    if num == int(num):
        num = int(num)
    return num

def clean_name(name):
    return re.sub(r'\?|!|,|\'|\"', '', name.replace(' ', '-').lower())

def download_skill_image(character, skill_name, skill_type, base_dir):
    name = clean_name(skill_name)
    dir = 'images/skills/%s' % character.replace('-', '')
    path = '%s/%s-%s.webp' % (dir, name, skill_type)
    if not os.path.exists(base_dir + '/' + dir):
        os.mkdir(base_dir + '/' + dir)
    with open(base_dir + '/' + path, 'wb') as f:
        url = 'https://hsr.honeyhunterworld.com/img/%s/%s-%s_icon.webp' % (skill_type, name, skill_type)
        res = requests.get(url, headers={'User-Agent': ua.random}, timeout=30)
        f.write(res.content)
    return path

def download_image(path, asset_id, img_type, base_dir):
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