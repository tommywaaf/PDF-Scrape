import os
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from urllib.parse import urlparse
from collections import deque

# setup
base_url = "https://www.westboylston-ma.gov/"
base_domain = urlparse(base_url).netloc  # we'll use this to filter links
visited_links = set()
options = Options()
options.headless = False

# Setup Chrome options
prefs = {
    "download.default_directory": "./pdfs",  # Modify this path to your desired folder
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "plugins.always_open_pdf_externally": True
}
options.add_experimental_option('prefs', prefs)

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)

# Function to check if URL serves a PDF
def is_pdf(url):
    try:
        response = requests.head(url)
        return response.headers['Content-Type'] == 'application/pdf'
    except Exception as e:
        print(f"Exception encountered while checking if url is pdf: {e}")
        return False

# Function to download the PDF
def download_pdf(url):
    response = requests.get(url)
    file_name = os.path.join('pdfs', url.split("/")[-1])
    with open(file_name, 'wb') as file:
        file.write(response.content)
    print(f"Downloaded: {url}")

def bfs_crawl(url, depth_limit=10):
    queue = deque([(url, 0)])  # (link, depth)

    while queue:
        url, depth = queue.popleft()
        if depth > depth_limit:  # limit to prevent infinite crawling
            continue

        if url in visited_links:
            continue
        visited_links.add(url)

        driver.get(url)
        # Check if the driver is still within the base_domain after loading the page
        if urlparse(driver.current_url).netloc != base_domain:
            print(f"Redirected outside of domain: {driver.current_url}")
            continue

        time.sleep(2)  # Wait for the JavaScript to execute
        print(f"Visiting: {url}")

        links = driver.find_elements(By.TAG_NAME, "a")
        print(f"Found {len(links)} links")  # Print the number of links found

        for link in links:
            try:
                href = link.get_attribute("href")
                if href is None or 'mailto' in href or urlparse(href).netloc != base_domain:
                    continue
                if is_pdf(href):
                    download_pdf(href)
                    continue
                # Print the link before visiting
                print(f"Link: {href}")
                # Only add to the queue if the link has the same base domain
                if href not in visited_links:
                    queue.append((href, depth+1))
            except Exception as e:
                print(f"Exception encountered: {e}")

bfs_crawl(base_url)
