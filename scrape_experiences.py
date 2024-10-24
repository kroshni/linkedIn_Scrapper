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

def clean_text(text): 
    if text is not None:
        text = text.replace('\u00b7', ' - ') 
        text = re.sub(r'\s*\n\s*', ' ', text)
    return text 

def extract_experience_html_data(url, file_name, driver):
    content = ''
    file_created = 2
    try:
        driver.get(url) 
        wait = WebDriverWait(driver, 10)
        experience_list = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="profile-content"]/div/div[2]/div/div/main/section/div[2]/div/div[1]/ul')))
        experience_html = experience_list.get_attribute('outerHTML') 
         
        with open(f"experience/{file_name}", 'w', encoding='utf-8') as f:
            if experience_html is None  or not isinstance(experience_html, str):
                f.write('')
            else: 
                f.write(experience_html)  
        file_created = 1               
        return experience_html, file_created

    except Exception as e:
        with open(f"experience/{file_name}", 'w', encoding='utf-8') as f: 
            f.write('')
        logging.error(f"Error extracting experience data: {url}, {e}", e) 
        logging.error(url) 
        return content, file_created

def extract_linkedin_experience(file_name): 
    with open(f"experience/{file_name}") as file:
        html_doc = file.read() 
    soup = BeautifulSoup(html_doc, 'html.parser') 
    
    experience_items = soup.find_all('li', class_ = 'artdeco-list__item') 
    experiences = [] 

    try: 
        for item in experience_items: 
            logo_url = ''
            position = ''
            job_type = ''
            duration = ''
            location = ''
            description = '' 
            company_name = ''
            skill_url = ''
            additinal_data = ''
            additional_all_data = []
            
            logo = item.find('div', class_="pvs-entity__image")
            try:
                logo_url = logo.find('img')['src']   
            except:
                logo_url = 'NA'  
            
            # # Extract company name and position
            company_tag = item.find('div', class_='t-bold')  
            position = company_tag.find('span') 
            if company_tag:
                position = position.get_text(strip=True)  
            
            type_tag = item.find('span', class_='t-14 t-normal')
            if type_tag:
                job_type = type_tag.find('span') 
                job_type = job_type.get_text(strip=True)  
            
            # # Extract employment duration
            duration_tag = item.find('span', class_='t-black--light')
            if duration_tag:
                duration = duration_tag.find('span') 
                duration = duration.get_text(strip=True)   
    
            # # Find location
            parent_div = item.find('div', class_="justify-space-between") 
            if parent_div:
                span_elements = parent_div.find_all('span', class_="t-black--light")
                if span_elements: 
                    location = span_elements[-1].find('span').get_text(strip=True) if span_elements else None  
            
            # Additional
            additional_div = item.find('div', class_="pvs-entity__sub-components") 
            if additional_div:
                additinal_data = additional_div.find_all('div', attrs={'data-view-name': 'profile-component-entity'}) 
            
            
            for ad in additinal_data:
                all_data = {}
                addition_data = ad.find('span', attrs={'aria-hidden':'true'})
                all_data['title'] = clean_text(addition_data.get_text(strip=True))
                addition_data = ad.find('span', class_="pvs-entity__caption-wrapper")
                all_data['duration'] = clean_text(addition_data.get_text(strip=True))
                additional_all_data.append(all_data)  
            
            skill_tag = item.find('li', class_="pvs-list__item--with-top-padding") 
            if skill_tag:
                description = skill_tag.get_text(strip=True) 
                
            try:
                company_linkedin = item.find('a')['href']  
            except:
                company_linkedin = None 
            
            try:
                company_li_id = company_linkedin.split('/')
                company_li_id = company_li_id[-2] if company_li_id[-1] == '' else company_li_id[-1]
            except:
                company_li_id = None 
            
                
            # skill_url = item.find('li', class_="pvs-list__item--with-top-padding")
            
            # if skill_url:
            #     skill_url = skill_url.find('a')['href']  
            
            
            try:
                company_name = item.find('span', class_="t-14")
                company_name = company_name.find('span').get_text(strip=True)  
            except:
                company_name = None 
            
            # try:
            #     date_range = item.find_element(By.CSS_SELECTOR, '.t-14.t-normal.t-black--light').text
            # except:
            #     date_range = None  

            from_date, to_date = None, None 

            if duration:
                date_parts = duration.split('·') 
                if len(date_parts) == 2:
                    from_date, to_date = date_parts[0].split('-')  
                    if 'Present' in to_date:
                        to_date = None
                else:
                    from_date = date_parts[0].strip()
                duration = duration.split('·')[1] if '·' in duration else None 
            
            # print(description, additional_all_data, company_linkedin, company_name, from_date, to_date, company_li_id)
            
            experiences.append({
                'company_logo': clean_text(logo_url),
                'position': clean_text(position),
                'type': clean_text(job_type),
                'duration': clean_text(duration),  
                'location': clean_text(location),
                'description': description,
                # 'skill_url': clean_text(skill_url),
                'additional_data': additional_all_data, 
                "companyURL": clean_text(company_linkedin),
                "company_name": clean_text(company_name), 
                "startDate": clean_text(from_date),
                "endDate": clean_text(to_date),   
                "company_li_id": clean_text(company_li_id)
            })  
            
        return experiences

    except Exception as e:
        logging.error("Error extracting data at experience time:  %s", e)  
        return experiences 



# extract_linkedin_experience('_in_bala-nathan-95b8181.html')

















 