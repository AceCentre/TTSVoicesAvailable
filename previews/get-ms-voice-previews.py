from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json

def scrape_voice_previews():
    url = "https://speech.microsoft.com/portal/voicegallery"

    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)

    driver.get(url)

    # Wait for the voice cards to load
    # Increase the timeout to 30 seconds
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.CLASS_NAME, "voice-card"))
    )

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()

    voice_previews = {}
    voice_divs = soup.find_all('div', {'class': 'voice-card'})

    for div in voice_divs:
        voice_id = div.find('div', {'class': 'voice-card-name'}).get('title')
        wav_url = div.find('audio').get('src')
        voice_previews[voice_id] = wav_url

    with open('voice_previews.json', 'w') as f:
        json.dump(voice_previews, f)

scrape_voice_previews()
