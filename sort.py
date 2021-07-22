import re
import os
import time
import json
import datetime
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from pipeit import *

for file_paths in os.walk(os.path.abspath('.')):
    file_paths = file_paths[2]; break
file_paths = file_paths | Filter(lambda x:x[-4:] == 'html') | list
file_paths.sort(key = lambda x:int(x[:x.index('.')]))


full_time_list = []
full_speed_list = []
full_text_list = []
full_id_set = set()
full_data_list = []

try:
    with open('full_text_list.txt','r',encoding='utf-8') as f:
        full_text_list = f.readlines()
    with open('full_data_list.txt','r',encoding='utf-8') as f:
        full_data_list = json.loads(f.read())
    for item in full_data_list:
        full_id_set.add(item['nickname'])
except:
    pass

for file_path in file_paths:
    with open(file_path,'r',encoding='utf-8') as f:
        html = f.read().replace('\u200b\u200b\u200b\u200b','')
    last_edit_time = os.stat(file_path).st_mtime
    last_edit_time = datetime.datetime.strptime(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_edit_time)), '%Y-%m-%d %H:%M:%S').astimezone(datetime.timezone(datetime.timedelta(hours=8)))

    soup = BeautifulSoup(html, 'lxml')
    tag_details = soup.find_all('div', {'class':'WB_detail'})

    numbers_pat = re.compile('[\d]+')
    period_text_pat = re.compile('[\d]+秒前 ')

    # post frequency
    max_search_time_period = ''
    period_length, period_num, period_speed = 0, 0, 0
    for index, weibo_detail in enumerate(tag_details[::-1]):
        last_time = period_text_pat.search(str(weibo_detail))
        if max_search_time_period == '':
            if not last_time:
                continue
            max_search_time_period = last_time.group()       
        else:
            if last_time and max_search_time_period not in str(weibo_detail):
                period_length = int(numbers_pat.search(last_time.group()).group())
                period_num = len(tag_details) - index
                if period_length != 0:
                    period_speed = round(period_num / period_length, 2)
                break
            continue
    full_time_list.append(last_edit_time)
    full_speed_list.append(period_speed)
    break

# detail statistics
options = webdriver.ChromeOptions()
# options.add_argument('--headless')
# options.add_argument('--disable-gpu')
driver = webdriver.Chrome('./chromedriver.exe', options=options)
driver.set_window_size(1920, 1080)
session = requests.session()

cover_img_pat = re.compile('background-image:url(.+?)')
no_others = None
for file_path in file_paths:
    if int(file_path[:file_path.index('.')]) <= 26:
        continue
    with open(file_path,'r',encoding='utf-8') as f:
        html = f.read().replace('\u200b\u200b\u200b\u200b','')
    print(f'Processing {file_path} ', end = '')
    soup = BeautifulSoup(html, 'lxml')
    tag_details = soup.find_all('div', {'class':'WB_detail'})

    for index, weibo_detail in enumerate(tag_details):
        weibo_data = {}
        fix_time = period_text_pat.search(str(weibo_detail))
        if fix_time:
            fix_time = int(numbers_pat.search(fix_time.group()).group())
        else:
            fix_time = 0
        weibo_data['last_edit_time'] = str(last_edit_time)[:-6]
        weibo_data['fix_time'] = fix_time
        weibo_data['post_time'] = str(last_edit_time - datetime.timedelta(seconds = fix_time))[:-6]
        text = weibo_detail.find('div', {'class': 'WB_text'}).text
        text = text.replace('...展开全文c', '').replace('','').replace('吴亦凡超话','').strip()
        text += '\n'
        weibo_data['text'] = text
        info = weibo_detail.find('div', {'class': 'WB_info'}).find('a')
        weibo_data['href'] = info.get('href')
        weibo_data['nickname'] = info.get('title')
        weibo_data['already_have'] = False
        uid = numbers_pat.search(weibo_data['href'])
        weibo_data['uid'] = uid.group() if uid else ''

        if weibo_data['nickname'] in full_id_set:
            weibo_data['already_have'] = True
            weibo_data['default_cover'] = True
            weibo_data['default_bg'] = True
            weibo_data['following'] = 0
            weibo_data['fans'] = 0
            weibo_data['weibo_num'] = 0
            weibo_data['further_url'] = ''
            weibo_data['register_date'] = '2021-01-01'
            continue

        driver.get(f"{weibo_data['href']}&is_all=1")
        driver.implicitly_wait(8)
        time.sleep(5)
        user_html = driver.execute_script("return document.documentElement.outerHTML")

        cover_img_pat = re.compile('background-image:url\(.+?profile_cover.+?\)')
        cover_result = cover_img_pat.search(user_html)
        default_cover = False
        default_bg = False
        if cover_result:
            if cover_result.group() == 'background-image:url(//img.t.sinajs.cn/t5/skin/public/profile_cover/001.jpg)':
                default_cover = True

        bg_img_pat = re.compile('<link type="text/css" rel="stylesheet" charset="utf-8" href=".+?skin.css.+?>')
        bg_img_url_pat = re.compile('.WB_miniblog{background:url\(".+?bg_page.+?"\)')
        bg_result = bg_img_pat.search(user_html)
        if bg_result:
            url = re.search('href=".+?"', bg_result.group()).group()[8:-1]
            html = session.get(f'http://{url}')
            bg_img_result = bg_img_url_pat.search(html.text)
            if bg_img_result:
                if bg_img_result.group() == '.WB_miniblog{background:url("images/body_bg.jpg?id=201503261330")  no-repeat top center;}.S_page .WB_miniblog{background:url("images/body_bg_page.jpg?id=201503261330")':
                    default_bg = True
        weibo_data['default_cover'] = default_cover
        weibo_data['default_bg'] = default_bg

        cap_digit_pat = re.compile('<strong class="W_f18">[\d]+</strong>')
        cap_digit_2_pat = re.compile('>[\d]+<')
        digits = cap_digit_pat.findall(user_html)
        following, fans, weibo_num = 0, 0, 0
        if len(digits) >= 3:
            following = int(cap_digit_2_pat.search(digits[0]).group()[1:-1])
            fans = int(cap_digit_2_pat.search(digits[1]).group()[1:-1])
            weibo_num = int(cap_digit_2_pat.search(digits[2]).group()[1:-1])

        weibo_data['following'] = following
        weibo_data['fans'] = fans
        weibo_data['weibo_num'] = weibo_num
        weibo_data['register_date'] = '2021-01-01'
        weibo_data['further_url'] = ''
        try:
            driver.find_element_by_css_selector("[class='WB_cardmore S_txt1 S_line1 clearfix']").click()
            time.sleep(1)
            driver.implicitly_wait(5)
            weibo_data['further_url'] = driver.current_url
            user_html2 = driver.execute_script("return document.documentElement.outerHTML")
            register_date = re.search(' [\d]{4}-[\d]{1,2}-[\d]{1,2} ', user_html2)
            if register_date:
                register_date = register_date.group()[2:-2]
                weibo_data['register_date'] = register_date

            full_id_set.add(weibo_data['nickname'])
            full_text_list.append(text)
            full_data_list.append(weibo_data)
        except exception as e:
            print('ERROR' , e)
        print(f'.', end = '')

    with open('full_text_list.txt','w',encoding='utf-8') as f:
        f.writelines(full_text_list)
    with open('full_data_list.txt','w',encoding='utf-8') as f:
        f.write(json.dumps(full_data_list))
    print(' done.')
