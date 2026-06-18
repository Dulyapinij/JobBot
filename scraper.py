import time
import pandas as pd
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

def classify_job(title):
    t = title.upper()
    tags = []
    if "SCIENTIST" in t: tags.append("Data Scientist")
    if "ANALYST" in t or "ANALYSIS" in t: tags.append("Data Analyst")
    if "ENGINEER" in t and "DATA" in t: tags.append("Data Engineer")
    if "SOFTWARE ENGINEER" in t or "DEVELOPER" in t or "PROGRAMMER" in t: tags.append("Software Developer")
    if "SYSTEM ANALYST" in t or "SA" == t: tags.append("System Analyst")
    return " & ".join(tags) if tags else "IT Related"

def scrape_jobsdb(keywords, target_pages=10):
    driver = get_driver()
    results = []
    seen_links = set()
    for kw in keywords:
        print(f"\n JobsDB: ขุดคีย์เวิร์ด [{kw}]")
        url = f"https://th.jobsdb.com/th/search-jobs/{kw.replace(' ', '-')}-jobs?sort=createdAt"
        driver.get(url)
        for page in range(1, target_pages + 1):
            print(f"  หน้า {page}...", end="", flush=True)
            try:
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'article')))
                driver.execute_script("window.scrollTo(0, 800);")
                time.sleep(1)
                cards = driver.find_elements(By.CSS_SELECTOR, 'article')
                count = 0
                for card in cards:
                    try:
                        title_elem = card.find_element(By.CSS_SELECTOR, '[data-automation="jobTitle"]')
                        link = title_elem.get_attribute('href').split('?')[0]
                        if link not in seen_links:
                            results.append({
                                "Source": "JobsDB", "Title": title_elem.text,
                                "Company": card.find_element(By.CSS_SELECTOR, '[data-automation="jobCompany"]').text,
                                "Link": link, "Category": classify_job(title_elem.text)
                            })
                            seen_links.add(link)
                            count += 1
                    except: continue
                print(f" +{count}")
                try:
                    next_btn = driver.find_element(By.CSS_SELECTOR, 'a[aria-label="Next"]')
                    driver.execute_script("arguments[0].scrollIntoView();", next_btn)
                    time.sleep(1); next_btn.click(); time.sleep(4)
                except: break
            except: break
    driver.quit()
    return results

def scrape_blognone(max_pages=20):
    driver = get_driver()
    results = []
    seen_links = set()
    print(f"\nBlognone: เริ่มขุดแบบกวาดทุกหน้า (1-{max_pages})")
    
    for page in range(1, max_pages + 1):
        url = f"https://jobs.blognone.com/search?page={page}"
        print(f" หน้า {page}...", end="", flush=True)
        driver.get(url)
        
        try:
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '/job/')]")))
            time.sleep(2)

            cards = driver.find_elements(By.XPATH, "//a[contains(@href, '/job/')]")
            count = 0
            for card in cards:
                try:
                    link = card.get_attribute('href').split('?')[0]
                    if "/job/" in link and "/company/" in link and link not in seen_links:
                        title = card.find_element(By.TAG_NAME, "h3").text
                        
                        try:
                            company = card.find_element(By.XPATH, ".//h3/following-sibling::div").text
                        except:
                            company = "Tech Company"
                        
                        results.append({
                            "Source": "Blognone",
                            "Title": title,
                            "Company": company,
                            "Link": link,
                            "Category": classify_job(title)
                        })
                        seen_links.add(link)
                        count += 1
                except: continue
            print(f" +{count}")
            if count == 0: break
        except: break
            
    driver.quit()
    return results

if __name__ == "__main__":
    kws = ["iot", "DevOps", "FullStack", "Front end", "Back end", "ERP", "Tester",
    "BigData", "Data Warehouse", "Data Analyst", "Data Architect", "Data Engineer",
    "Data Science", "AI", "Deep Learning", "Machine Learning", "System Analyst",
    "Blockchain", "cyber security", "Web Developer", "App Developer", "Software Engineer"]
    
    jobsdb_list = scrape_jobsdb(kws, target_pages=15)
    blognone_list = scrape_blognone(max_pages=25)
    
    all_jobs = jobsdb_list + blognone_list
    df = pd.DataFrame(all_jobs)
    df.to_csv("jobs_phase1_final.csv", index=False, encoding="utf-8-sig")
    
    print(f"\n สำเร็จ! รวมได้ทั้งหมด {len(df)} งานที่ไม่ซ้ำกัน")