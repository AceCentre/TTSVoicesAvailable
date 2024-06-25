import requests
from bs4 import BeautifulSoup
import json


def extract_voices(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    voices_list = []

    # Find all voice entries on the page
    voices = soup.find_all('div', class_='voice')
    for voice in voices:
        voice_data = {}
        voice_data['gender'] = voice.get('data-gender', 'Unknown')
        
        # Extract name and image with error checking
        identity = voice.find('div', class_='identity')
        if identity:
            voice_data['name'] = identity.find('p', class_='name').text if identity.find('p', class_='name') else 'No name available'
            voice_data['image'] = identity.find('img').get('src') if identity.find('img') else 'No image available'
        else:
            voice_data['name'] = 'No name available'
            voice_data['image'] = 'No image available'

        # Extract all demo items
        demos = voice.find_all('div', class_='demo-item')
        voice_data['demos'] = []
        for demo in demos:
            demo_data = {}
            demo_data['age'] = demo.find('p', {'data-label': 'Age'}).text if demo.find('p', {'data-label': 'Age'}) else 'Age unknown'
            demo_data['quality'] = demo.find('p', {'data-label': 'Quality'}).text if demo.find('p', {'data-label': 'Quality'}) else 'Quality unknown'
            sound_player = demo.find('div', class_='sound-player')
            if sound_player:
                demo_data['mp3'] = sound_player.get('data-mp3', 'No audio available')
                demo_data['lang'] = sound_player.get('data-lang', 'Language unknown')
            voice_data['demos'].append(demo_data)
        
        voices_list.append(voice_data)

    return voices_list

# URL to scrape
url = 'https://www.acapela-group.com/voices/repertoire/'
voices_list = extract_voices(url)

# Save the data to a JSON file
with open('acapela-voices.json', 'w', encoding='utf-8') as f:
    json.dump(voices_list, f, ensure_ascii=False, indent=4)

print("Data has been written to 'acapela-voices.json'")
