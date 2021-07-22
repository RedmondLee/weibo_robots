from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import datetime

name_count = 0
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--disable-gpu')
driver = webdriver.Chrome('./chromedriver.exe',chrome_options=options)
while True:
    try:
        driver
        driver.get("your.website.com/1008084859662b1e491eaefde4d08a0d9cc82a/super_index")
        driver.implicitly_wait(20)
        time.sleep(16)
        driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
        driver.implicitly_wait(20)
        time.sleep(3)
        driver.execute_script('window.scrollTo(0,document.body.scrollHeight);')
        driver.implicitly_wait(20)
        webelement = driver.execute_script("return document.documentElement.outerHTML")
        with open(f'{name_count}.html','w',encoding = 'utf-8') as f:
            f.write(webelement)
        name_count += 1
        fail = False
    except:
        name_count += 1
        fail = True
    current_time = datetime.datetime.now()
    print(current_time, name_count, len(webelement), 'Fail' if fail == True else "")
    next_min = datetime.datetime(current_time.year, current_time.month,current_time.day,current_time.hour,current_time.minute,0)
    next_min += datetime.timedelta(seconds = 60)
    sleep_time = next_min - current_time
    time.sleep(sleep_time.total_seconds())
