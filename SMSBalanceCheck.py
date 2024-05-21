from datetime import datetime
import logging
import time
import re
from SGTAMProdTask import SGTAMProd
from config import SGTAM_log_config, email
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def create_driver():
    # this function create and return web driver object, so it can be used multiple times later.
    # No need to explicitly declared multiple times
    try:
        logging.info('Create web driver object.')
        print('Create web driver object.')
        chrome_path = 'D:/SGTAM_DP/Working Project/SMS Gateway/chrome_driver/chromedriver'
        service = Service(chrome_path)
        driver = webdriver.Chrome(service=service)
        logging.info('Web driver object created.')
        print('Web driver object created.')
        return driver
    except Exception as e:
        logging.info('Failed to create web driver object.')
        print('Failed to create web driver object.')
        raise e

def login_onewaysms(driver):
    # login the webpage
    try:
        logging.info("Login OneWaySms platform")
        print("Login OneWaySms platform")
        url = 'https://sms.onewaysms.sg/Default.aspx'
        username_keys = 'GFK'
        password_keys = 'GFK8161511'
        
        driver.maximize_window()
        driver.set_page_load_timeout(5)
        driver.get(url)
        wait = WebDriverWait(driver,3)
        username = wait.until(EC.presence_of_element_located((By.ID, 'C_login1_txtLoginName')))
        username.send_keys(username_keys)
        password = driver.find_element(By.ID, 'C_login1_txtPassword')
        password.send_keys(password_keys)
        login_btn = driver.find_element(By.ID, 'C_login1_btnLogin')
        login_btn.click()
        logging.info("Login successfully")
        print("Login successfully")
    except Exception as e:
        logging.info('Login failed.')
        print('Login failed.')
        raise e
    
def get_credit_balance(driver):
    # Extract the balance from webpage and return it as output
    try:
        logging.info('Getting credit balance.')
        print('Getting credit balance.')
        wait = WebDriverWait(driver,3)
        credit_balance = wait.until(EC.presence_of_element_located((By.ID, 'ctl00_C_menumy1_Label1'))).text
        lines = credit_balance.split('\n')
        for line in lines:
            if 'Credit Balance' in line:
                match = re.search(r'\d+$', line)
                if match:
                    return int(match.group())
        logging.info('Credit balance retrieved.')
        print('Credit balance retrieved.')
    except Exception as e:
        logging.info('Failed to retrieved credit balance.')
        print('Failed to retrieved credit balance.')
        raise e

def logout(driver):
    #log out
    try:
        nav_bar = driver.find_element(By.ID, 'ddtopmenubar')
        nav_bar_ul = nav_bar.find_element(By.TAG_NAME, 'ul')
        nav_bar_li = nav_bar_ul.find_elements(By.TAG_NAME, 'li')
        for li in nav_bar_li:
            a_tag = li.find_element(By.TAG_NAME, 'a')
            if a_tag.text == 'Logout':
                a_tag.click()
                break
        logging.info('Log out sucessfully.')
        print('Log out sucessfully.')
    except Exception as e:
        logging.info('Error at log out.')
        print('Error at log out.')
        raise e

def main():
    driver = None
    credit_balance = None
    try:
        # setup logging
        logging.basicConfig(
            filename= f"log\{datetime.now().strftime('%Y%m%d%H%M')}_SMSBalanceCheck.log",
            format='%(asctime)s %(levelname)s %(message)s',
            level=logging.INFO
        )
        s = SGTAMProd()
        SGTAM_log_config['statusFlag'], SGTAM_log_config['logID']  = s.insert_tlog(**SGTAM_log_config)

        # Create and assign driver object to variable driver
        driver = create_driver()

        # Execute all the functions here
        login_onewaysms(driver)
        credit_balance = get_credit_balance(driver)
        logout(driver)
        driver.quit()

        if credit_balance <= 100:
            print(f"Balance is low, please top up.\nCredit Balance: {credit_balance}")
            logging.info(f"Balance is low, please top up.\nCredit Balance: {credit_balance}")
            SGTAM_log_config['statusFlag'] = 3
            SGTAM_log_config['logMsg'] = f'Credit balance is at minimum threshold of 100.'
            email['to'] = 'hweesuen.ong@gfk.com,Caryn.Peh@gfk.com'
            #email['to'] = f'SIRIKORN.CHATPHATTHANANAN@gfk.com'
            email['cc'] = 'SGTAMDPTeam@gfk.com'
            email['subject'] = f'SMS Gateway Credit Balance.'
            email['body'] = f'SMS gateway credit balance is LOW.\nPlease check and assist to top up.\n\nCredit Balance: {credit_balance}'
            s.send_email(**email)
            s.update_tlog(**SGTAM_log_config)
        else:
            print(f"Balance is above minimum level of 100.\nCredit Balance: {credit_balance}")
            logging.info(f"Balance is above minimum level of 100.\nCredit Balance: {credit_balance}")
            SGTAM_log_config['statusFlag'] = 1
            SGTAM_log_config['logMsg'] = f'Credit balance is ok and above 100.'
            email['to'] = 'hweesuen.ong@gfk.com,Caryn.Peh@gfk.com'
            #email['to'] = f'SIRIKORN.CHATPHATTHANANAN@gfk.com'
            email['cc'] = 'SGTAMDPTeam@gfk.com'
            email['subject'] = f'SMS Gateway Credit Balance.'
            email['body'] = f'SMS gateway credit balance is ok and above 100.\n\nCredit Balance: {credit_balance}'
            s.send_email(**email)
            s.update_tlog(**SGTAM_log_config)

    except Exception as e:
        logging.info(e)
        print(e)
        SGTAM_log_config['statusFlag'] = 2
        SGTAM_log_config['logMsg'] = f'There is an error.\n{e}'
        email['to'] = 'SGTAMDPTeam@gfk.com'
        #email['to'] = f'SIRIKORN.CHATPHATTHANANAN@gfk.com'
        email['cc'] = None
        email['subject'] = f'[ERROR] SMS Gateway Credit Balance.'
        email['body'] = f'There is an error.\n{e}'
        s.send_email(**email)
        s.update_tlog(**SGTAM_log_config)
    finally:
        logging.info('Enter finally clause, check and close any web driver in the background.')
        print('Enter finally clause, check and close any web driver in the background.')
        if driver:
            driver.quit()
            logging.info('Detected web driver and closed it.\nProcess ended.')
            print('Detected web driver and closed it.\nProcess ended.')
        else:
            logging.info('No web driver is running in the background.\nProcess ended.')
            print('No web driver is running in the background.\nProcess ended.')

if __name__ == '__main__':
    main()


