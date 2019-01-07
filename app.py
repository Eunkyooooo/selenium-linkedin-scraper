import time
import csv
import sys
import os
from datetime import datetime as dt
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException


def get_url(name):
    url_list = {'login':'https://www.linkedin.com/uas/login',
                'main':'https://www.linkedin.com/feed/',
                'search_base':'https://www.linkedin.com/search/results/people/?facetGeoRegion=%5B"us%3A0"%5D&origin=FACETED_SEARCH'}
    return url_list[name]

def init_selenium():
    """
    Configure chrome driver as headless
    """

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1420,1080')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    return webdriver.Chrome(chrome_options=chrome_options)

def wait_page(check_page):
    browser.get(check_page)
    check_interval = 1  # second
    check_retry = 10
    succeed = False
    for i in range(check_retry):
        if browser.current_url == check_page:
            succeed = True
            break
        else:
            time.sleep(check_interval)
    return succeed

def wait_element_by_xpath(xpath, multiple=False):
    """
    If multiple set as True, it will try to find all element matches the xpath
    and return list of elements.
    """

    try:
        if multiple:
            element = WebDriverWait(browser, MAX_WAIT_TIME).until(
                EC.presence_of_all_elements_located((By.XPATH, xpath)))
        else:
            element = WebDriverWait(browser, MAX_WAIT_TIME).until(
                EC.presence_of_element_located((By.XPATH, xpath)))
    except TimeoutException:
        element = False
    return element

def wait_element_until_visible(element):
    try:
        WebDriverWait(browser, MAX_WAIT_TIME).until(EC.visibility_of(element))
        return True
    except TimeoutException:
        return False

def wait_send_key(element, value):
    for char in value:
        element.send_keys(char)
        time.sleep(0.2)
    try:
        WebDriverWait(browser, MAX_WAIT_TIME).until(
            lambda browser: element.get_attribute('value') == value)
        return True
    except TimeoutException:
        return False

def login():
    """
    Login to linkedin is needed
    """

    print("Login with your Linkedin ID !!")
    user = input("ID: ")
    pwd = input("Password: ")
    print("Logging in...")
    login_url = get_url("login")
    browser.implicitly_wait(3)
    if not wait_page(login_url):
        return False
    #print(browser.current_url) # This is for debugging
    browser.find_element_by_id('username').send_keys(user)
    browser.find_element_by_id('password').send_keys(pwd)
    login_btn = wait_element_by_xpath("//div[@class='login__form_action_container ']/button[@class='btn__primary--large from__button--floating']")
    if isinstance(login_btn, bool):
        print("Error: check your Internet access !!!")
        return False
    else:
        login_btn.click()

    # Cheking login is succeed or not
    if wait_page(get_url("main")):
        print("Login complete with " + user + " !!!")
        return True
    else:
        print("Error: Login falied with " + user + " !!!")
        return False

def filter_blacklist(company_list):
    """
    Filter company from the list
    """
    blacklist_file = "etc/blacklist.txt"
    blacklist = []
    try:
        with open(workspace + "/" + blacklist_file, 'r') as f:
            blacklist_reader = f.readlines()
            for item in blacklist_reader:
                blacklist.append(item.lower().strip())
        for item in blacklist:
            print(item + " is listed in blacklist !!!")
        return list(filter(lambda item: item.lower().strip() not in blacklist, company_list))
    except IOError:
        print("Error: "+ blacklist_file + " doesn't exists !!! ")
        sys.exit(1)

def get_company_list():
    """
    Parse csv to get company list
    """
    input_file = 'input.csv'
    company_list = []

    try:
        with open(workspace + "/" +input_file, 'r') as f:
            csv_reader = csv.DictReader(f,  delimiter=',')
            for info in csv_reader:
                company_list.append(info['company_name'].strip())
        return filter_blacklist(set(company_list))
    except IOError:
        print("Error: "+ input_file + " doesn't exists !!! ")
        sys.exit(1)

def get_company_info():
    """
    Get company info (company name, auto_search_company, business, employees_in_us)
    """

    # This base_url contains us location
    base_url = get_url("search_base")
    succeed_result = []
    error_result = []

    try:
        for num, company  in enumerate(get_company_list()):
            try:
                print("Check#" + str(num+1) + ": " + company)
                wait_page(base_url)
                cur_companies_btn = wait_element_by_xpath("//button[@aria-controls='current-companies-facet-values']")
                input_box = wait_element_by_xpath("//input[@placeholder='Add a current company']")
                cur_companies_btn.click()

                if wait_element_until_visible(input_box):
                    wait_send_key(input_box, company)
                    input_box.click()
                    auto_search_res = wait_element_by_xpath("//ul[@class='type-ahead-results ember-view']/li", True)
                    if isinstance(auto_search_res, bool):
                        # Can't find company name from LinkedIn, Error code 1
                        print("Can't find " + company + " on LinkedIn...")
                        error_result.append({'company': company, "error_code": 1})
                        continue
                    else:
                        auto_search_res = auto_search_res[0]

                    auto_search_parse = str(auto_search_res.text).split('\n')
                    auto_search_company = auto_search_parse[0]

                    # Compare given company and auto_search_company from LinkedIn
                    if company.strip().lower() != auto_search_company.strip().lower():
                        print(company + " and " + auto_search_company + " is different...")
                        error_result.append({'company': company, "error_code": 2})
                        continue

                    if len(auto_search_parse) > 1:
                        auto_search_business = auto_search_parse[1]
                    else:
                        auto_search_business = "None"
                    print("auto-search name: " + auto_search_company)
                    auto_search_res.click()

                    # There are 3 apply btn on this page, we are only using visible apply button
                    apply_btn = wait_element_by_xpath("//form[@aria-label='Filter results by: Current companies']//button[@data-control-name='filter_pill_apply']")
                    if wait_element_until_visible(apply_btn):
                        apply_btn.click()
                    else:
                        # Failed to find apply button
                        print("Error: No apply button to click...")
                        error_result.append({'company': company, "error_code": 3})
                        continue

                    print("waiting...")
                    time.sleep(1) # It takes time to update numbers on page
                    employees_in_us = wait_element_by_xpath("//h3[@class='search-results__total t-14 t-black--light t-normal pl5 pt4 clear-both']").text.split()[1]
                    print("Employess in US: " + employees_in_us)
                    succeed_result.append({'company':company,
                                           'business': auto_search_business,
                                           'employees_in_us': int(employees_in_us.replace(',',''))})
                else:
                    # If input box not visible
                    print("Error: Input box is not visible...")
                    error_result.append({'company': company, "error_code": 4})
                    continue
            except StaleElementReferenceException:
                print("Error: Unknown error...")
                error_result.append({'company': company, "error_code": 5})
                continue

    except KeyboardInterrupt:
        # Handle SIGINT (Ctrl+C)
        print("Stop requested !!!")
    return succeed_result, error_result

def save_result(result, directory, file):
    """
    Save result, it will make result file under given directory
    """

    result_dir = 'result/' + directory
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    try:
        with open(workspace + "/" + result_dir + "/" + file, 'w') as f:
            if len(result):
                field_names = list(result[0].keys())
                csv_writer = csv.DictWriter(f, fieldnames=field_names, delimiter=',')
                csv_writer.writeheader()
                for row in result:
                    csv_writer.writerow(row)
    except IOError:
        print("Error: can't write or create " + result_dir + "/" + file + " !!! ")
        sys.exit(1)

if __name__ == '__main__':
    workspace = os.getcwd()
    browser = init_selenium()
    MAX_WAIT_TIME = 15
    if login():
        succeed_result, error_result = get_company_info()
        result_dir = dt.now().strftime("%Y%m%d%H%M")
        save_result(succeed_result, result_dir, 'succeed.csv')
        save_result(error_result, result_dir, 'error.csv')
        print("Done!!")
    else:
        print("Can't start without login !!!")
