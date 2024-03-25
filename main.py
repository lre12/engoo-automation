import json
import os
import time

from selenium import webdriver
from tempfile import mkdtemp

from selenium.webdriver import Keys
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By


def login(driver: WebDriver, email: str, pwd: str) -> WebDriver:
    driver.get('https://engoo.co.kr/app/login')
    time.sleep(5)
    inputs = driver.find_elements(by=By.TAG_NAME, value="input")
    driver.execute_script("arguments[0].scrollIntoView();", inputs[0])
    inputs[0].send_keys(email)
    driver.execute_script("arguments[0].scrollIntoView();", inputs[1])
    inputs[1].send_keys(pwd)
    buttons = driver.find_elements(by=By.TAG_NAME, value="button")
    login_button = [b for b in buttons if b.accessible_name == "로그인"]
    driver.execute_script("arguments[0].scrollIntoView();", login_button[0])
    login_button[0].send_keys(Keys.ENTER)
    time.sleep(2)
    driver.execute_script("window.open('about:blank', '_blank');")
    handles = driver.window_handles
    driver.switch_to.window(handles[1])
    return driver


def get_reservation_data(driver: WebDriver, tutor_ids: list[str]) -> list[dict]:
    results = []
    for tutor_id in tutor_ids:
        driver.get(f"https://engoo.co.kr/tutors/{tutor_id}")
        time.sleep(2)
        alist = driver.find_elements(by=By.TAG_NAME, value="a")
        reservation_data = [a.get_attribute("data-info") for a in alist if a.text == "예약하기"]
        if reservation_data:
            reservation_data = [json.loads(d) for d in reservation_data]
            results.append({tutor_id: reservation_data})

    return results


def handler(event=None, context=None):
    options = webdriver.ChromeOptions()
    service = webdriver.ChromeService("/opt/chromedriver")

    options.binary_location = '/opt/chrome/chrome'
    options.add_argument("--headless=new")
    options.add_argument('--no-sandbox')
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1280x1696")
    options.add_argument("--single-process")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-dev-tools")
    options.add_argument("--no-zygote")
    options.add_argument(f"--user-data-dir={mkdtemp()}")
    options.add_argument(f"--data-path={mkdtemp()}")
    options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    options.add_argument("--remote-debugging-port=9222")

    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(20)
    email = os.environ.get('ENGOO_EMAIL')
    pwd = os.environ.get('ENGOO_PWD')
    driver = login(driver=driver, email=email, pwd=pwd)
    tutor_ids = os.environ.get('ENGOO_TUTOR_IDS')
    tutor_ids = tutor_ids.split(",")
    reservation_data = get_reservation_data(driver=driver, tutor_ids=tutor_ids)

    if not reservation_data:
        raise Exception("no slot")


    result_text = []
    for data in reservation_data:
        id = data.keys()[0]
        url = f"https://engoo.co.kr/tutors/{id}"

        slot_info_list = []
        for slot in data[id]:
            info = f"date: {slot['lesson_date']}\nstart_time: {slot['scheduled_start_time']}"
            slot_info_list.append(info)
        slot_infos = "\n\n".join(slot_info_list)
        result_text.append(f"url : {url} \n\n slot info : {slot_infos}")

    return result_text


if __name__=="__main__":
    handler()