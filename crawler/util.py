# coding: utf-8

import os
import re
import requests

from fake_useragent import UserAgent

srs_assets_url = 'https://starrailstation.com/assets'
ua = UserAgent()

def is_buff_skill(desc):
    return ' extended ' in desc \
        or ' extend ' in desc \
        or ' increases ' in desc \
        or ' increase ' in desc \
        or ' gain ' in desc \
        or re.match(r'.*\+\d+(\.\d+)?%.*', desc) is not None

def is_team_skill(desc):
    return ' all enemies' in desc

def format_percent_number(num):
    num = float(round(num * 100, 2))
    if num == int(num):
        num = int(num)
    return num

def download_skill_image(character, skill_name, skill_type, base_dir):
    name = re.sub(r'\?|!|,|\'|\"', '', skill_name.replace(' ', '-').lower())
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