from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import os
import pickle
import tempfile

from .config import *

def make_headless_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")

    # Auto-download the compatible driver version
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    return driver


def make_headful_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")

    # Auto-download the compatible driver version
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    return driver


def get_amazon_login_from_driver(driver) -> str:
    temp_dir = tempfile.mkdtemp()
    cookie_file = os.path.join(temp_dir, "amazon_cookies.pkl")
    try:
        driver.get("https://www.amazon.com/your-orders/orders") # generic orders page, forces login
        
        if MANUAL_LOGIN_CONFIRMATION:
            input("Please log in to Amazon and press Enter after you are fully logged in...")
        else:
            print("Please log in to Amazon. Waiting for login to complete...")
            # Wait for the "Your Orders" heading to appear, which indicates successful login
            WebDriverWait(driver, LOGIN_TIMEOUT_S).until(
                EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Your Orders')]"))
            )
        
        with open(cookie_file, "wb") as f:
            pickle.dump(driver.get_cookies(), f)
    finally:
        driver.quit()
    return cookie_file


def login_to_amazon_from_cookies(driver, login_cookie_file_path):
    driver.get("https://www.amazon.com/your-orders/")
    with open(login_cookie_file_path, "rb") as f:
        cookies = pickle.load(f)
    for cookie in cookies:
        driver.add_cookie(cookie)
    driver.get("https://www.amazon.com/your-orders/")


def do_manual_amazon_login() -> str:
    driver = make_headful_driver()
    try:
        cookie_path = get_amazon_login_from_driver(driver)
    finally:
        driver.quit()
    return cookie_path
