import pandas as pd
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def get_driver():
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

df = pd.read_csv("jobs_phase1_final.csv")
print(f"พร้อมขุด JD และ Location สำหรับ {len(df)} งาน")

df['Description'] = ""
df['Location'] = ""

driver = get_driver()

try:
    for index, row in df.iterrows():
        print(f"[{index + 1}/{len(df)}] ขุดข้อมูล: {row['Title'][:25]}...", end="", flush=True)
        
        try:
            driver.get(row['Link'])
            wait = WebDriverWait(driver, 8)
            
            desc = "N/A"
            loc = "N/A"

            if "jobsdb.com" in row['Link']:
                try:
                    desc = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-automation="jobAdDetails"]'))).text
                except: pass
                try:
                    loc = driver.find_element(By.CSS_SELECTOR, 'span[data-automation="job-detail-location"], a[href*="/jobs/in-"]').text
                except: pass

            elif "blognone.com" in row['Link']:
                try:
                    desc = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="JobDetail"], div[class*="Description"]'))).text
                except: pass
                try:
                    loc = driver.find_element(By.CSS_SELECTOR, 'div[itemprop="address"]').text
                except: pass

            df.at[index, 'Description'] = desc
            df.at[index, 'Location'] = loc
            print(f" (Loc: {loc[:15]}...)")

        except Exception as e:
            print(" ข้าม (Error)")

        if (index + 1) % 25 == 0:
            df.to_csv("jobs_phase2_checkpoint.csv", index=False, encoding="utf-8-sig")

finally:
    df.to_csv("jobs_master_final.csv", index=False, encoding="utf-8-sig")
    driver.quit()
    print("\n Phase 2 เสร็จสมบูรณ์! ข้อมูลครบทั้ง JD และสถานที่ทำงาน")