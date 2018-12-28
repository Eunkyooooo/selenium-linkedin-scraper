import time
import csv
import sys
from datetime import datetime as dt
from selenium import webdriver

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

def login():
    """
    Login to linkedin is needed
    """

    login_url = "https://www.linkedin.com/uas/login"
    succeed_url = "https://www.linkedin.com/feed/"
    check_interval = 1
    check_retry = 10
    succeed = False

    print("Login with your Linkedin ID !!")
    user = input("ID: ")
    pwd = input("Password: ")
    print("Logging in...")
    browser.implicitly_wait(3)
    browser.get(login_url)

    #print(browser.current_url) # This is for debugging
    browser.find_element_by_id('username').send_keys(user)
    browser.find_element_by_id('password').send_keys(pwd)
    browser.find_element_by_xpath("//div[@class='login__form_action_container ']/button[@class='btn__primary--large from__button--floating']").click()

    # Cheking login is succeed or not
    for i in range(check_retry):
        if browser.current_url == succeed_url:
            succeed = True
            break
        else:
            time.sleep(check_interval)
    if succeed:
        print("Login complete with " + user + " !!!")
    else:
        print("Error: Login falied with " + user + " !!!")
    return succeed

def filter_blacklist(company_list):
    """
    Filter company from the list
    """

    blacklist_file = "/etc/blacklist.txt"
    blacklist = []
    try:
        with open(workspace + blacklist_file, 'r') as f:
            blacklist_reader = f.readlines()
            for item in blacklist_reader:
                blacklist.append(item.strip())
        for item in blacklist:
            print(item + " is listed in blacklist !!!")
        return list(filter(lambda item: item not in blacklist, company_list))
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
        with open(workspace + input_file, 'r') as f:
            csv_reader = csv.DictReader(f,  delimiter=' ')
            for info in csv_reader:
                company_list.append(info['company_name'])
        return filter_blacklist(set(company_list))
    except IOError:
        print("Error: "+ input_file + " doesn't exists !!! ")
        sys.exit(1)

def get_company_info():
    """
    Get company info (company name, business, employees_in_us)
    """

    # This base_uri contains us location
    base_uri = 'https://www.linkedin.com/search/results/people/?facetGeoRegion=%5B"us%3A0"%5D&origin=FACETED_SEARCH'
    result = []

    for company in get_company_list():
        browser.get(base_uri)
        cur_companies_btn = browser.find_element_by_xpath("//form[@aria-label='Current companies']/button[@aria-controls='current-companies-facet-values']")
        input_box = browser.find_element_by_xpath("//input[@placeholder='Add a current company']")
        cur_companies_btn.click()

        # If input box is not visible, following steps will have error
        if input_box.is_displayed():
            input_box.send_keys(company)
            # Prevent clicked before company name sent to input_box
            while input_box.get_attribute('value') != company:
                time.sleep(check_interval)
            input_box.click()
            # TODO(hwvwvi@): check if given company name is not exists
            # TODO(hwvwvi@): Sometimes company name and auto_search_company is different even company name is correct on input_box
            auto_search_res = browser.find_elements_by_xpath("//ul[@class='type-ahead-results ember-view']/li")[0]
            auto_search_parse = str(auto_search_res.text).split('\n')
            auto_search_company = auto_search_parse[0]
            auto_search_business = auto_search_parse[1]
            print("Check auto-search company: " + auto_search_company)
            auto_search_res.click()

            # There are 3 apply btn on this page, we are only using visible apply button
            apply_btn = browser.find_elements_by_xpath("//button[@data-control-name='filter_pill_apply']")
            cache_uri = browser.current_url
            for btn in apply_btn:
                if btn.is_displayed():
                    btn.click()

            print("waiting...")
            while cache_uri == browser.current_url:
                time.sleep(check_interval)

            employees_in_us = browser.find_element_by_xpath("//h3[@class='search-results__total t-14 t-black--light t-normal pl5 pt4 clear-both']").text.split()[1]
            result.append({'company':company,
                          'business': auto_search_business,
                          'employees_in_us': employees_in_us})
    return result

def save_result(result):
    """
    Save result on file, name will be timestamp (ex. 201812151547.csv)
    """

    result_file = dt.now().strftime("%Y%m%d%H%M") + '.csv'
    try:
        with open(workspace + "result/" + result_file, 'w') as f:
            field_names = ['company', 'business', 'employees_in_us']
            csv_writer = csv.DictWriter(f, fieldnames=field_names, delimiter='\t')
            csv_writer.writeheader()
            for row in result:
                csv_writer.writerow(row)
    except IOError:
        print("Error: can't write or create " + result_file + " !!! ")
        sys.exit(1)

if __name__ == '__main__':
    # Workspace in docker container
    workspace = '/usr/workspace/'
    check_interval = 1 # second
    browser = init_selenium()
    if login():
        save_result(get_company_info())
        print("Done!!")
    else:
        print("Can't start without login !!!")
