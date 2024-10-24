from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import re
import urllib.parse
import time 
import logging

def extract_html_data(url, file_name, driver):
    
    content = ''
    file_created = 2
    
    try:
        driver.get(url)
        time.sleep(5) 
        edu_data = ''
        education_html = driver.find_elements(By.CSS_SELECTOR, '.pvs-list__container') 
        for elem in education_html: 
            edu_data = elem.get_attribute("outerHTML")  
            with open(f"education/{file_name}", 'w', encoding='utf-8') as f:
                if edu_data is None  or not isinstance(edu_data, str):
                    f.write('')
                else: 
                    f.write(edu_data)  
        file_created = 1       
        return edu_data, file_created

    except Exception as e:
        with open(f"education/{file_name}", 'w', encoding='utf-8') as f: 
            f.write('')
        logging.error("Error extracting education data: %s", e) 
        logging.error(url) 
        return content, file_created
        # print(driver.page_source) 

def extract_linkedin_education(file_name): 
    with open(f"education/{file_name}") as file:
        html_doc = file.read() 
    soup = BeautifulSoup(html_doc, 'html.parser')
        
    education_items = soup.select('.artdeco-list__item')
    education_data = []

    for item in education_items:
        insti_li_id = ''
        institution_name = 'NA'
        degree = 'NA'
        date_range = 'NA'
        start_year, end_year = '', ''
        try: 
            instiURL = item.find('a') 
            if instiURL:
                instiURL = instiURL['href']  
            else:
                instiURL = '' 
            
            insti_li_id = instiURL.split('/') if instiURL else []
            if len(insti_li_id) > 0:
                insti_li_id = insti_li_id[-2] if insti_li_id[-1] == '' else insti_li_id[-1]  
            
            institution_name_div = item.find('div', class_="display-flex align-items-center mr1 hoverable-link-text t-bold")
            if institution_name_div:
                institution_name_span = institution_name_div.find('span')
                institution_name = institution_name_span.get_text(strip=True) if institution_name_span else None 

            degree_span = item.find('span', class_="t-14 t-normal")
            if degree_span:
                degree_span_element = degree_span.find('span') 
                degree = degree_span_element.get_text(strip=True) if degree_span_element else None  

            date_range_span = item.find('span', class_="t-14 t-normal t-black--light") 
            if date_range_span:
                date_range = date_range_span.find('span', class_="pvs-entity__caption-wrapper") 
                date_range = date_range.get_text(strip=True) 
                if '-' in date_range:
                    start_year, end_year = date_range.split('-')
                else:
                    end_year = date_range
                
        except Exception as e:
            # Handle the exception or log the error
            logging.error("An error occurred in education: %s", e) 
            
        
        # institution_name = item.find('span', {'class': 'visually-hidden'}).text.strip()
        # degree = item.find('span', {'class': 'visually-hidden'}).find_next('span', {'class': 'visually-hidden'}).text.strip()
        # date_range = item.find('span', {'class': 'visually-hidden'}).find_next('span', {'class': 'visually-hidden'}).find_next('span', {'class': 'visually-hidden'}).text.strip()
 
        education_data.append({
            "start_year": start_year,
            "end_year": end_year,
            "instiURL": instiURL,
            "insti_li_id": insti_li_id,
            "institution_name": institution_name,
            "degree": degree
        })  
        
    return education_data


# extract_linkedin_education('_in_bala-nathan-95b8181.html')