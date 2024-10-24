import pandas as pd
from time import sleep
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
# import pymongo
from scrape_experiences import extract_experience_html_data, extract_linkedin_experience
from scrape_education import extract_linkedin_education, extract_html_data
from scrape_post import extract_post_html_data, extract_user_post_data
import time
from PIL import Image
import pytesseract   
import requests
import os
from bs4 import BeautifulSoup  
import re
import urllib.parse
from datetime import date 
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, NoSuchElementException 
import logging 
from selenium.webdriver.chrome.options import Options
 

# Configure the logging
logging.basicConfig(
    filename='error.log',          # Log file name
    level=logging.ERROR,           # Logging level
    format='%(asctime)s - %(levelname)s - %(message)s', # Log format
    datefmt='%Y-%m-%d %H:%M:%S'    # Date and time format
) 
 
try:   
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
    print("WebDriver started successfully.")
except Exception as e:
    logging.error("WebDriver initialization failed: %s", e) 
    
    
# Path to your .env file
env_file_path = '.env'

# Key and new value for the cookie
cookie_key = 'cookie'

VERIFY_LOGIN_ID = "global-nav__primary-link"
REMEMBER_PROMPT = 'remember-me-prompt__form-primary'

# Function to check if CAPTCHA is present
def is_captcha_present(image_path):
    ''' Use OCR to check if CAPTCHA is detected in the image '''
    try:
        text = pytesseract.image_to_string(Image.open(image_path))
        return "quick security check" in text.lower() 
    except Exception as e:
        logging.error("Error in captcha present: ", e) 
        print("Error in captcha present: ", e)  

# Function to save a screenshot and check for CAPTCHA
def check_captcha():
    ''' Function to save a screenshot and check for CAPTCHA '''
    try: 
        try:
            mobile_verify = driver.find_element(By.ID, "register-verification-phone-number")
            if mobile_verify:
                user_df.at[user_index, 'status'] = 'Banned'   
                user_df.to_csv('user_list.csv', index=False)    
        except Exception as e:
            print("Not asking for mobile verification")
        
        file_name_unique = time.time()
        screenshot_path = f'screenshot/screenshot{int(file_name_unique)}.png'
        driver.save_screenshot(screenshot_path)
        return is_captcha_present(screenshot_path)
    except Exception as e:
        logging.error("Please hit this url in project folder: check captcha function in main.py file", e) 
        print("Please hit this url in project folder,  check captcha function in main.py file")
        exit()

def login(driver, email=None, password=None, cookie=None, timeout=10):
    try: 
        if cookie is not None:
            return _login_with_cookie(driver, cookie)

        driver.get('https://www.linkedin.com/login')
        time.sleep(1)
        username = driver.find_element(By.ID, "username")
        username.send_keys(email)
        password_field = driver.find_element(By.ID, "password")
        password_field.send_keys(password)
        return driver.find_element(By.XPATH, "//button[@type='submit']").click()
    except Exception as e:
        logging.error("Error in login: ", e) 
        print("Error in login: ", e)   

def _login_with_cookie(driver, cookie): 
    driver.get("https://www.linkedin.com/")
    driver.add_cookie({
        "name": "li_at",
        "value": cookie,
        "domain": ".linkedin.com"
    })
    driver.get("https://www.linkedin.com/feed/")  # Navigate to a LinkedIn page after adding the cookie
    time.sleep(10) 

    # Get the current URL
    current_url = driver.current_url

    # Check if it is redirected
    if 'feed' in current_url:
        return True
    else:
        return False 

def focus(driver):
    driver.execute_script('alert("Focus window")')
    driver.switch_to.alert.accept()

def wait(duration):
    sleep(int(duration))

def extract_text(element):
    try: 
        return element.get_text(strip=True) if element else None
    except Exception as e:
        logging.error("Error in extract_text function in main.py file: ", e) 
        print("Error in extract_text function in main.py file: ", e) 
        return element

# Function to save user posts
def url_to_filename(url: str) -> str:
    try: 
        # Parse the URL to get the path and query components
        parsed_url = urllib.parse.urlparse(url)
        path = parsed_url.path
        query = parsed_url.query

        # Combine path and query into one string
        url_path = path
        if query:
            url_path += f'?{query}'

        # Replace non-alphanumeric characters (except dots and hyphens) with underscores
        filename = re.sub(r'[^\w\-_\.]', '_', url_path)
        filename = filename.replace('_recent-activity_all_','')
        # Ensure the filename is not too long (e.g., limit to 255 characters)
        max_filename_length = 255
        filename = filename[:max_filename_length]

        # Add a file extension based on the content type, if needed
        # For this example, we'll use .html as a generic extension
        # if not filename.endswith('.html'):
        filename += '.html'

        return filename
    except Exception as e:
        logging.error("Error in url_to_filename function in main.py file: ", e) 
        print("Error in url_to_filename function in main.py file: ", e) 
        return False 

def update_env_variable(env_file_path, key, new_value):
    # Read the existing .env file
    with open(env_file_path, 'r') as file:
        lines = file.readlines()
    
    # Write the updated content to a temporary list
    updated_lines = []
    key_found = False
    
    for line in lines:
        if line.startswith(f"{key}="):
            updated_lines.append(f"{key}={new_value}\n")
            key_found = True
        else:
            updated_lines.append(line)
    
    # If the key was not found, add it to the end
    if not key_found:
        updated_lines.append(f"{key}={new_value}\n")
    
    # Write the updated content back to the .env file
    with open(env_file_path, 'w') as file:
        file.writelines(updated_lines)

# Task for scraping a LinkedIn profile

def scraper_data(url, driver, user_name, user_id):
    ''' Scrapping data '''
    driver.get(url)
    # focus(driver)
    wait(5)

    try: 
        top_panels = driver.find_elements(By.XPATH,'//*[@id="profile-content"]/div/div[2]/div/div/main/section[1]/div[2]/div[2]')
        # about_html = top_panels[0].get_attribute('outerHTML')
        # name = top_panels[0].find_elements(By.XPATH,"*")[0].text.split("\n")[0]
        user_location = top_panels[0].find_element(By.XPATH,'//*[@id="profile-content"]/div/div[2]/div/div/main/section[1]/div[2]/div[2]/div[2]/span[1]').text
    except Exception as e:
        user_location = ''  
    
    ''' User personal Info '''
    # User linkedIn Id  
    user_linkedin_id = url.split('/') 
    user_linkedin_id = user_linkedin_id[-1]   
    user_bio = '' 
    try:
        # Wait for the element to be present before accessing it
        user_bio_element = user_bio = driver.find_element(By.CSS_SELECTOR, '.text-body-medium.break-words')
        user_bio = user_bio_element.text
    except NoSuchElementException:
        logging.error(f"Could not locate user bio element.{user_name}")
        print("Could not locate user bio element {user_name}.")
    except Exception as e:
        logging.error(f"Error while extracting user bio.{user_name}: ", e)
        print(f"Error while extracting user bio {user_name}: {e}")
        
    user_about = '' 
    
    try: 
        user_about_div = driver.find_element(By.CSS_SELECTOR, '.artdeco-card.pv-profile-card.break-words') 
        user_about = user_about_div.find_element(By.CSS_SELECTOR, '.pvs-header__title') 
        user_about = user_about.find_element(By.CSS_SELECTOR, '.visually-hidden').text
        
        if "About" in user_about: 
            user_about = user_about_div.find_element(By.CSS_SELECTOR, '.OcxAhhUlSrHZsdLRXuCWCdHGDbVuyVmjJKI')
            user_about = user_about.find_element(By.CSS_SELECTOR, '.visually-hidden').text
    except NoSuchElementException as e:
        logging.error(f"Element User about not found: {user_name},{e}") 
    except Exception as e:
        logging.error(f"Error in User about extraction: {user_name},{e}") 
    
    # Initialize variables to store followers and connections
    followers = ''
    connections = ''
    try:
        # Locate the <ul> element by its class name
        ul_element = driver.find_element(By.CSS_SELECTOR, '.ZNhzNTROzFhvvUeecdiHKFaAJvunAfLgg.XkdzhLXlchajYwCPqdSyKJpSEEprBbfQI')

        # Find all <li> elements within the <ul>
        li_elements = ul_element.find_elements(By.TAG_NAME, 'li') 

        # Loop through each <li> element to find the relevant information
        for li in li_elements:
            text = li.text
            if 'followers' in text:
                followers = li.find_element(By.CLASS_NAME, 't-bold').text
            elif 'connections' in text:
                connections = li.find_element(By.CLASS_NAME, 't-bold').text  
    except Exception as e:
        logging.error(f"Error in User followers, connections extraction: {user_name},{e}") 
        print(f"Error while extracting user followers, connections {user_name}: {e}") 
    
    wait(5) 
    
    file = url_to_filename(f'{url}')
    education_html, education_file_created = extract_html_data(f'{url}/details/education/', file, driver) 
    # education = extract_linkedin_education(file) 
    
    wait(5)
    # experiences, experience_html = extract_linkedin_experience(f'{url}/details/experience', driver) 
    experience_html, experience_file_created = extract_experience_html_data(f'{url}/details/experience/', file, driver) 
    # experiences = extract_linkedin_experience(file)

    # wait(5)
    users_post_html, users_post_file_created  = extract_post_html_data(f'{url}/recent-activity/all/', file, driver) 
    
    # post_data = extract_user_post_data(url, file, user_name) 
    
    html = { 
        "experience_html": experience_html,
        "education_html": education_html 
    }

    # data = {
    #     "experience" : experiences,
    #     "name" : user_name,
    #     "location" : user_location,
    #     "education" : education,
    #     "post" : post_data,
    # }
    
    personal = {
        "li_url": url,
        "user_linkedin_id": user_linkedin_id,
        "bio": user_bio,
        "followers_count": followers,
        "connections_count": connections,
        "location": user_location, 
        "name": user_name, 
        "about": user_about 
    }  
    
    try:
        ''' Checking record already exist or not if exist then update otherwise insert it '''
        # Define your filter and the new data
        # filter_query = {'linkedin_url': url}  # The filter to check if the record exists, e.g., by _id
        # new_data = {'$set': {"user_id": user_id, "linkedin_url": url, "user_name": user_name, "data": html, "dumps": data}}  # Data to insert or update
        # new_data = {'$set': {"user_id": user_id, "linkedin_url": url, "user_name": user_name, "data": data, "dumps": html, "personal": personal}}  # Data to insert or update
        # new_data = {'$set': {"user_id": user_id, "linkedin_url": url, "user_name": user_name, "dumps": html, "personal": personal}}  # Data to insert or update

        # Perform the upsert operation
        # result = all_linked_data.update_one(filter_query, new_data, upsert=True)

       

        # Check the result
        # if result.matched_count > 0: 
        #     record_saved = 1 
        # elif result.upserted_id is not None: 
        #     record_saved = 1
        # else:
        #     record_saved = 2
        record_saved = 1 
        return record_saved, education_file_created, experience_file_created
        # test_linkedin_data.insert_one({"data": html, "dumps": data})
        # print(f"Data for {name} inserted successfully into MongoDB.")
    except Exception as e:
        logging.error("An error occurred while inserting data into MongoDB: %s", e) 
        return 2, education_file_created, experience_file_created 
 
counter = 1
 
try: 
    while True:
        current_url = driver.current_url 
        
        if 'feed' in current_url: 
            
            new_cookie_value =  driver.get_cookie('li_at')['value']
            # Update the .env file
            update_env_variable(env_file_path, cookie_key, new_cookie_value)
            
            ''' Read data from csv file and copy in another file to track status of scrapping ''' 
            if os.path.exists('scrapping_status_all.csv'):
                csv_file = "scrapping_status_all.csv"  
                df = pd.read_csv(csv_file)
                df.drop_duplicates(inplace = True) 
                pending_posts_df = df[df['common'] == 'Not Started']   
                
                for index, row in pending_posts_df.iterrows():   
                    if row['Link'] != '':
                        linkd_url = row['Link']  
                        status, education_f_created, experience_f_created, users_post_f_created = scraper_data(linkd_url, driver, row['Lead Full Name'], index) 
                        result_output = "Yes" if status == 1 else "No"
                         
                        df.at[index, 'education_file'] = "Yes" if experience_f_created == 1 else "No"
                        df.at[index, 'experience_file'] = "Yes" if education_f_created == 1 else "No" 
                        df.at[index, 'record_saved'] = "Yes" if status == 1 else "No"
                        print("Index: ", index, "Exp: ", experience_f_created, "Edu: ",  education_f_created, "Post: ",  users_post_f_created, "Inserted: ",  status)
                        ''' Update user record has been saved successfully ''' 
                        df.to_csv('User.csv', index=False)  
                        
                        if index%2 == 0: 
                            time.sleep(5)  
                    else:
                        break  
                driver.quit()       
            else:
                csv_file = os.getenv('read_data_from_csv')
                df = pd.read_csv(csv_file)  
                df_selected = df[['Link']].copy()        
                df_selected.loc[:, 'experience_file'] = 'Not Started'
                df_selected.loc[:, 'education_file'] = 'Not Started' 
                df_selected.loc[:, 'record_saved'] = 'Not Started' 
                df_selected.loc[:, 'experience_data'] = 'Not Started'
                df_selected.loc[:, 'education_data'] = 'Not Started' 
                 
                output_file = 'scrapping_status_all.csv'
                df_selected.to_csv(output_file, index=False)  
            
        # elif check_captcha():
        #     print("CAPTCHA detected! Please solve it manually.")
        #     time.sleep(10)   
            
        else: 
            
            ''' Login with cookie '''
            try: 
                # driver.get("https://www.linkedin.com/")
                # driver.get("https://www.linkedin.com/feed/") 
                # cookie = driver.get_cookie('li_at')   
                cookie = os.getenv('cookie') 
                if cookie:
                    if _login_with_cookie(driver, cookie):
                        pass
                    else:
                        ''' Fetch active users '''
                        user_csv_file = "user_list.csv"  
                        user_df = pd.read_csv(user_csv_file, dtype={'status': str})
                        user_df.drop_duplicates(inplace = True) 
                        active_users = user_df[user_df['status'].isna() | (user_df['status'] == '') | (user_df['status'] == 'In progress')]  

                        # Create an iterator for the DataFrame rows
                        user_iterator = active_users.iterrows()
                        user_index, user_row = next(user_iterator)
                        user_email = user_row['user_name']
                        user_password = user_row['user_password']  
                        
                        ''' Updating status of current user_id as 'in_progress' '''
                        user_df.at[user_index, 'status'] = 'In progress'   
                        user_df.to_csv('user_list.csv', index=False)   
                            
                        login(driver, user_email, user_password) 
                        check_captcha()
                else:
                    ''' Fetch active users '''
                    user_csv_file = "user_list.csv"  
                    user_df = pd.read_csv(user_csv_file, dtype={'status': str})
                    user_df.drop_duplicates(inplace = True) 
                    active_users = user_df[user_df['status'].isna() | (user_df['status'] == '') | (user_df['status'] == 'In progress')]  

                    # Create an iterator for the DataFrame rows
                    user_iterator = active_users.iterrows()
                    user_index, user_row = next(user_iterator)
                    user_email = user_row['user_name']
                    user_password = user_row['user_password']  
                    
                    ''' Updating status of current user_id as 'in_progress' '''
                    user_df.at[user_index, 'status'] = 'In progress'   
                    user_df.to_csv('user_list.csv', index=False)   
                        
                    login(driver, user_email, user_password) 
                    check_captcha()
                print("Waiting for login...")
                time.sleep(30)  
            except Exception as e:
                cookie = ''
             
        counter = counter+1
except Exception as e: 
    # driver.quit()
    logging.error("Issue in scrapping")
finally: 
    # driver.quit()
    ''' Saved record in db ''' 
    def save_scrape_data(url, user_id): 
    
        file = url_to_filename(f'{url}') 
        education = extract_linkedin_education(file)  
        experiences = extract_linkedin_experience(file)   

        data = {
            "experience" : experiences, 
            "education" : education 
        }  
 
        education_saved = 1
        experiences_saved = 1    
            
        return experiences_saved, education_saved

    if os.path.exists('scrapping_status_all.csv'):
        csv_file = "scrapping_status_all.csv"  
        df = pd.read_csv(csv_file)
        df.drop_duplicates(inplace = True) 
        pending_posts_df = df[df['record_saved'] == 'Yes']   
            
        for index, row in pending_posts_df.iterrows():   
            if row['Link'] != '':
                linkd_url = row['Link']  
                experiences_status, education_status, post_status = save_scrape_data(linkd_url, index)  
                df.at[index, 'record_saved'] = "Updated exp, edu and post" if education_status == 1 else "Not updated exp, edu and post"
                df.at[index, 'experience_data'] = "Yes" if experiences_status == 1 else "No"
                df.at[index, 'education_data'] = "Yes" if education_status == 1 else "No" 
                
                print("Index: ", index, "Exp: ", experiences_status, "Edu: ",  education_status, "Post: ",  post_status)
                # print(index, experiences_status, education_status, post_status)
                ''' Update user record has been saved successfully ''' 
                df.to_csv('scrapping_status_all.csv', index=False)  
                
                if index%10 == 0: 
                    time.sleep(5)  

    
