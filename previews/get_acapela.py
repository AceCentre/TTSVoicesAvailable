import requests
from bs4 import BeautifulSoup
import json

def extract_voices(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    voices_list = []

    voices = soup.find_all('div', class_='voice')
    for voice in voices:
        identity = voice.find('div', class_='identity')
        if identity:
            voice_name = identity.find('p', class_='name').text if identity.find('p', class_='name') else 'No name available'
            gender = voice.get('data-gender', 'Unknown')
        else:
            continue  # Skip if no identity found

        # Extract demo items for preview_audio, language codes, and quality
        demos = voice.find_all('div', class_='demo-item')
        for demo in demos:
            sound_player = demo.find('div', class_='sound-player')
            if sound_player:
                preview_audio = sound_player.get('data-mp3', 'No audio available')
                lang = sound_player.get('data-lang', 'Language unknown')
                quality = demo.find('p', {'data-label': 'Quality'}).text if demo.find('p', {'data-label': 'Quality'}) else 'Quality unknown'
                if lang != 'Language unknown':
                    voice_data = {
                        "id": f"{voice_name}-{quality}".replace(" ", "-").lower(),
                        "language_codes": [lang],
                        "name": voice_name,
                        "gender": gender,
                        "preview_audio": preview_audio,
                        "quality": quality
                    }
                    voices_list.append(voice_data)
                break  # Assuming we take the first demo item's data

    return voices_list

# URL to scrape
url = 'https://www.acapela-group.com/voices/repertoire/'
voices_data = extract_voices(url)

# Save the data to a JSON file with the engine-software format
filename = 'acapela-voice-browser.json'
with open(filename, 'w', encoding='utf-8') as f:
    json.dump(voices_data, f, ensure_ascii=False, indent=4)

print(f"Data has been written to '{filename}'")
