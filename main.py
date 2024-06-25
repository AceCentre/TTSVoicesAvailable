from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from tts_wrapper import PollyTTS, PollyClient, GoogleTTS, GoogleClient, MicrosoftTTS, MicrosoftClient, WatsonTTS, WatsonClient, ElevenLabsTTS, ElevenLabsClient, WitAiTTS, WitAiClient, MMSTTS, MMSClient
import os
import json
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# In-memory cache for voice data
cache = {}

# List of engines for dropdown
engines_list = ["polly", "google", "microsoft", "watson", "elevenlabs", "witai", "mms", "other"]

class Voice(BaseModel):
    id: str
    language_codes: List[str]
    name: str
    gender: Optional[str] = None

def get_client(engine: str):
    logger.info(f"Creating client for engine: {engine}")
    if engine == 'polly':
        region = os.getenv('POLLY_REGION')
        aws_key_id = os.getenv('POLLY_AWS_KEY_ID')
        aws_access_key = os.getenv('POLLY_AWS_ACCESS_KEY')
        logger.info(f"Polly credentials - Region: {region}, Key ID: {aws_key_id}")
        return PollyClient(credentials=(region, aws_key_id, aws_access_key))
    elif engine == 'google':
        creds_path = os.getenv('GOOGLE_CREDS_PATH')
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
        filtered_voices = [voice for voice in filtered_voices if lang_name in voice.get('language', '')]
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
def get_voices(engine: Optional[str] = Query(None, enum=engines_list), lang_code: Optional[str] = None, lang_name: Optional[str] = None, name: Optional[str] = None, gender: Optional[str] = None, page: Optional[int] = 1, page_size: Optional[int] = 50):
    other_voices_file = 'other_voices.json'

    if engine:
        voices = get_cached_voices(engine.lower())
        if not voices:
            if engine.lower() == 'other':
                with open(other_voices_file, 'r') as file:
                    voices = json.load(file)
            else:
                tts = get_tts(engine.lower())
                if not tts:
                    raise HTTPException(status_code=400, detail="Invalid engine")
                voices = tts.get_voices()
            cache_voices(engine.lower(), voices)
    else:
        voices = []
        for eng in engines_list:
            eng_voices = get_cached_voices(eng)
            if not eng_voices:
                if eng == 'other':
                    with open(other_voices_file, 'r') as file:
                        eng_voices = json.load(file)
                else:
                    tts = get_tts(eng)
                    if tts:
                        eng_voices = tts.get_voices()
                cache_voices(eng, eng_voices)
            voices.extend(eng_voices)

    filtered_voices = filter_voices(voices, lang_code, lang_name, name, gender)

    start = (page - 1) * page_size
    end = start + page_size
    paginated_voices = filtered_voices[start:end]

    return [Voice(**voice) for voice in paginated_voices]

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
