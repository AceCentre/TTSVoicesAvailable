from fastapi import FastAPI, Query, HTTPException
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel
from tts_wrapper import PollyTTS, PollyClient, GoogleTTS, GoogleClient, MicrosoftTTS, MicrosoftClient, WatsonTTS, WatsonClient, ElevenLabsTTS, ElevenLabsClient, WitAiTTS, WitAiClient, MMSTTS, MMSClient
import os
import json
from datetime import datetime, timedelta
import logging
from fuzzysearch import find_near_matches

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# In-memory cache for voice data
cache = {}

# List of engines for dropdown
engines_list = ["polly", "google", "microsoft", "watson", "elevenlabs", "witai", "mms", "acapela", "other"]

class Voice(BaseModel):
    id: str
    name: str
    gender: Optional[str] = None
    engine: str
    languages: List[Dict[str, Union[str, float]]] = []  # List of dictionaries for language code and lat-long pairs

def load_geo_data():
    with open('geo-data.json', 'r') as file:
        return json.load(file)

def find_geo_info(language_code, geo_data):
    for item in geo_data:
        if item["language_code"] == language_code:
            return item["latitude"], item["longitude"], item["language"]
    return 0.0, 0.0, 'Unknown' # Default values if no match is found

def load_voices_from_source(engine: str):
    other_voices_file = 'misc-misc.json'
    acapela_voices_file = 'acapela-acapela.json'
    voices = []
    geo_data = load_geo_data()  # Load geographical data

    if engine == 'other':
        with open(other_voices_file, 'r') as file:
            voices_raw = json.load(file)
            voices = [{"engine": item.get("engine", engine), **item} for item in voices_raw]
    elif engine == 'acapela':
        with open(acapela_voices_file, 'r') as file:
            voices_raw = json.load(file)
            voices = [{"engine": 'acapela', **voice} for voice in voices_raw]
    else:
        tts = get_tts(engine)
        if tts:
            try:
                voices_raw = tts.get_voices()
                voices = [{"engine": engine, **voice} for voice in voices_raw]
            except Exception as e:
                logging.info(f"Failed to get voices for engine {engine}: {e}")
                voices = [{"id": "error", "language_codes": [], "name": "Error fetching voices", "engine": engine}]
        else:
            raise HTTPException(status_code=400, detail="Invalid engine")

    # Add geographical data to each voice
    updated_voices = []
    for voice in voices:
        languages = []
        for lang_code in voice.get("language_codes", []):
            lat, long, language = find_geo_info(lang_code, geo_data)
            languages.append({"language_code": lang_code, "latitude": lat, "longitude": long, "language": language})
        updated_voice = voice.copy()  # Create a copy of the voice
        updated_voice["languages"] = languages
        updated_voices.append(updated_voice)  # Add the updated voice to the list
    
    return updated_voices

def get_client(engine: str):
    logger.info(f"Creating client for engine: {engine}")
    if engine == 'polly':
        region = os.getenv('POLLY_REGION')
        aws_key_id = os.getenv('POLLY_AWS_KEY_ID')
        aws_access_key = os.getenv('POLLY_AWS_ACCESS_KEY')
        return PollyClient(credentials=(region, aws_key_id, aws_access_key))
    elif engine == 'google':
        creds_path = os.getenv('GOOGLE_CREDS_PATH')
        google_creds_json = os.getenv("GOOGLE_CREDS_JSON")

        if not google_creds_json:
            raise ValueError("GOOGLE_CREDS_JSON environment variable is not set")
        
        if not creds_path:
            raise ValueError("GOOGLE_CREDS_PATH environment variable is not set")

        with open(creds_path, "w") as f:
            f.write(google_creds_json)
            f.close()

        logger.info(f"Google credentials path: {creds_path}")
        return GoogleClient(credentials=(creds_path))
    elif engine == 'microsoft':
        token = os.getenv('MICROSOFT_TOKEN')
        region = os.getenv('MICROSOFT_REGION')
        logger.info(f"Microsoft credentials - Token: {token}, Region: {region}")
        return MicrosoftClient(credentials=(token, region))
    elif engine == 'watson':
        api_key = os.getenv('WATSON_API_KEY')
        api_url = os.getenv('WATSON_API_URL')
        region = os.getenv('WATSON_REGION')
        instance_id = os.getenv('WATSON_INSTANCE_ID')
        logger.info(f"Watson credentials - API Key: {api_key}, API URL: {api_url}")
        return WatsonClient(credentials=(api_key, region, instance_id))
    elif engine == 'elevenlabs':
        api_key = os.getenv('ELEVENLABS_API_KEY')
        logger.info(f"ElevenLabs API Key: {api_key}")
        return ElevenLabsClient(credentials=(api_key))
    elif engine == 'witai':
        token = os.getenv('WITAI_TOKEN')
        logger.info(f"WitAi Token: {token}")
        return WitAiClient(credentials=(token))
    elif engine == 'mms':
        logger.info("Creating MMS client")
        return MMSClient()
    else:
        logger.error(f"Invalid engine: {engine}")
        return None

def get_tts(engine: str):
    client = get_client(engine)
    if engine == 'polly':
        return PollyTTS(client)
    elif engine == 'google':
        return GoogleTTS(client)
    elif engine == 'microsoft':
        return MicrosoftTTS(client)
    elif engine == 'watson':
        return WatsonTTS(client)
    elif engine == 'elevenlabs':
        return ElevenLabsTTS(client)
    elif engine == 'witai':
        return WitAiTTS(client)
    elif engine == 'mms':
        return MMSTTS(client)
    else:
        return None

def filter_voices(voices: List[Dict[str, Any]], lang_code: Optional[str] = None, lang_name: Optional[str] = None, name: Optional[str] = None, gender: Optional[str] = None) -> List[Dict[str, Any]]:
    filtered_voices = voices
    if lang_code:
        filtered_voices = [voice for voice in filtered_voices if lang_code in voice['language_codes']]
    if lang_name:
        filtered_voices = [
            voice for voice in filtered_voices 
            if any(find_near_matches(lang_name.lower(), lang.lower(), max_l_dist=1) for lang in voice.get('language', ''))
        ]
    if name:
        filtered_voices = [voice for voice in filtered_voices if name.lower() in voice['name'].lower()]
    if gender:
        filtered_voices = [voice for voice in filtered_voices if gender.lower() == voice['gender'].lower()]
    return filtered_voices

def cache_voices(engine: str, voices: List[Dict[str, Any]]):
    cache[engine] = {
        "data": voices,
        "timestamp": datetime.now()
    }

def get_cached_voices(engine: str):
    cached_data = cache.get(engine)
    if cached_data and (datetime.now() - cached_data['timestamp']) < timedelta(days=1):
        return cached_data['data']
    return None

@app.get("/voices", response_model=List[Voice])
def get_voices(engine: Optional[str] = Query(None, enum=engines_list), lang_code: Optional[str] = None, lang_name: Optional[str] = None, name: Optional[str] = None, gender: Optional[str] = None, page: Optional[int] = 1, page_size: Optional[int] = 50, ignore_cache: Optional[bool] = False):
    voices = []
    if engine:
        if not ignore_cache:
            voices = get_cached_voices(engine.lower())
        if not voices:
            voices = load_voices_from_source(engine.lower())
            if not ignore_cache:
                cache_voices(engine.lower(), voices)
    else:
        for eng in engines_list:
            if not ignore_cache:
                eng_voices = get_cached_voices(eng)
            if not eng_voices:
                try:
                    eng_voices = load_voices_from_source(eng)
                except Exception as e:
                    logger.error(f"Failed to fetch voices for engine {engine}: {e}")
                    continue
                if not ignore_cache:
                    cache_voices(eng, eng_voices)
            voices.extend(eng_voices)

    filtered_voices = filter_voices(voices, lang_code, lang_name, name, gender)

    #If page_size is 0, return all voices without pagination.
    if page_size == 0:
        paginated_voices = filtered_voices
    else:
        start = (page - 1) * page_size
        end = start + page_size
        paginated_voices = filtered_voices[start:end]

    return [Voice(**voice) for voice in paginated_voices]

if __name__ == '__main__':
    is_development = os.getenv('DEVELOPMENT') == 'True'
    if is_development:
        print("Loading credentials")
        from load_credentials import load_credentials
        load_credentials()

    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
