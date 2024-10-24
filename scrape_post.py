from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import re
import urllib.parse
import time
import re
import urllib.parse
from datetime import date 
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, NoSuchElementException
import json 
import logging
 

def remove_html_tags(html_string):
    try:
        soup = BeautifulSoup(html_string, 'html.parser')
        return soup.get_text()
    except Exception as e:
        return html_string 

def extract_post_html_data(linkedIn_url, file, driver):
    ''' Saving User Posts in HTML file '''
    driver.get(linkedIn_url) 
    time.sleep(5)
    
    content = ''
    file_created = 2
    
    try:
        # Scroll until no new content is loaded 
        while True:  
            show_more = driver.find_elements(By.CSS_SELECTOR, '.scaffold-finite-scroll__load-button')   
            if show_more:  
                try:   
                    show_more[0].click() 
                except Exception as e:
                    return False 
                time.sleep(5)
            else:
                break 
        time.sleep(5) 
         
        while True:
            # see_more = driver.find_elements(By.CSS_SELECTOR, '.feed-shared-inline-show-more-text__see-more-less-toggle')    
            see_more = driver.find_elements(By.CSS_SELECTOR, '.feed-shared-inline-show-more-text__dynamic-more-text')    
            try:
                if see_more:
                    # Click on each button
                    for button in see_more:
                        try:
                            # Scroll the element into view
                            driver.execute_script("arguments[0].scrollIntoView(true);", button)
                            time.sleep(1)  # Adjust sleep time if necessary
                            
                            # Click using JavaScript as a fallback
                            driver.execute_script("arguments[0].click();", button)
                            time.sleep(2)  # Adjust sleep time if necessary

                        except ElementClickInterceptedException as e:
                            logging.error("Click intercepted: %s", e) 
                            logging.error(linkedIn_url) 
                            # Scroll a bit more to bring the element fully into view
                            driver.execute_script("window.scrollBy(0, -100);")
                            time.sleep(2)  # Adjust sleep time if necessary
                            driver.execute_script("arguments[0].click();", button)

                        except StaleElementReferenceException as e:
                            logging.error("Stale element reference: %s", e) 
                            logging.error(linkedIn_url) 
                            break  # Refetch elements after the DOM has changed

                        except NoSuchElementException as e:
                            logging.error("No such element: %s", e) 
                            logging.error(linkedIn_url) 
                            break  # Refetch elements after the DOM has changed

                        except Exception as e:
                            logging.error("Error clicking button: %s", e) 
                            logging.error(linkedIn_url) 
                            break  # Handle any other exceptions
                else:
                    break
            except Exception as e:
                logging.error("Error at see more click on user post page: %s", e) 
                logging.error(linkedIn_url) 
            
        time.sleep(5)   
        
        posts_data = ''
        post_html = driver.find_elements(By.CSS_SELECTOR, '.pv-recent-activity-detail__core-rail') 
        for elem in post_html: 
            posts_data = elem.get_attribute("outerHTML")  
        
            with open(f"user_posts/{file}", 'w', encoding='utf-8') as f:
                if posts_data is None  or not isinstance(posts_data, str):
                    f.write('')
                else: 
                    f.write(posts_data) 
        file_created = 1    
        return posts_data, file_created
    except Exception as e: 
        logging.error("Error in post HTML extraction: %s", e)
        logging.error(linkedIn_url)  
        return content, file_created

def extract_user_post_data(linkedIn_url, file_name, user_name): 
    post_data = []  
    try:  
        with open(f"user_posts/{file_name}") as f:
            html_doc = f.read() 
        soup = BeautifulSoup(html_doc, 'html.parser') 
        post_items = soup.find_all('li', class_ = 'profile-creator-shared-feed-update__container') 

        for item in post_items:  
            post_url = 'NA'
            description = 'NA'
            images = []  
            post_time = 'NA'  
            
            try:
                # Post Url
                try:   
                    post_url = item.find('div', class_ = 'feed-shared-update-v2--minimal-padding')   
                    if post_url: 
                        post_url = post_url.get('data-urn')
                        post_url = f"https://www.linkedin.com/feed/update/{post_url}?updateEntityUrn=urn%3Ali%3Afs_updateV2%3A%28urn%3Ali%3Aactivity%3A7233737081255030784%2CFEED_DETAIL%2CEMPTY%2CDEFAULT%2Cfalse%29&lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base%3BjQls4V6JRiamaYSVoPKziw%3D%3D"
                except Exception as e:
                    logging.error("Error Post URL %s", e)
                    logging.error(linkedIn_url)  
                    
                # Extracting Description
                try:
                    description = item.find('span', class_ = "tvm-parent-container")
                    if description:
                        description = description.find('span')
                        description = description.get_text(strip=True)
                        description = remove_html_tags(description)
                        description = description.replace('"','\"')
                except Exception as e:
                    logging.error("Error at description time: %s", e)
                    logging.error(linkedIn_url) 
                
                # Time extraction
                post_time = item.find('span', class_ = "update-components-actor__sub-description")  
                try: 
                    if post_time: 
                        post_time = post_time.find('span').get_text(strip=True)  
                        post_time = post_time.split('•') 
                        post_time = post_time[0]  
                    else:
                        post_time = 'NA'
                except Exception as e:
                    logging.error("Error at Post time: %s", e)
                    logging.error(linkedIn_url)   
                 
            except Exception as e:
                # Handle the exception or log the error
                logging.error("An error in data extraction: %s", e)
                logging.error(linkedIn_url) 

            post_data.append({
                'post_url': post_url,
                'description': description, 
                'time': post_time, 
            })  
            
        return post_data
    except Exception as e:
        logging.error(f"Error Other at post data extarction:{user_name}, {e}") 
        return post_data