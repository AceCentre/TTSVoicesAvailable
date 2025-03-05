from fastapi import FastAPI, Query, HTTPException
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel
from tts_wrapper import (
    PollyTTS, PollyClient, 
    GoogleTTS, GoogleClient, 
    MicrosoftTTS, MicrosoftClient, 
    WatsonTTS, WatsonClient, 
    ElevenLabsTTS, ElevenLabsClient, 
    WitAiTTS, WitAiClient, 
    SherpaOnnxTTS, SherpaOnnxClient,
    PlayHTTTS, PlayHTClient)
import os
import json
from datetime import datetime, timedelta
import logging
from fuzzysearch import find_near_matches
import uvicorn

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

app = FastAPI()

# In-memory cache for voice data
cache = {}

# List of engines for dropdown - we update this im main
engines_list = [
    "polly", "google", "microsoft", "watson", "elevenlabs", 
    "witai", "sherpaonnx", "playht"
]


def load_tts_engines(directory):
    tts_engines = {}
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r') as file:
                engine_data = json.load(file)
                engine_name = filename.replace('.json', '')
                tts_engines[engine_name] = engine_data
    return tts_engines

def update_engines_list(engines_list, tts_engines):
    for engine_name in tts_engines.keys():
        if engine_name not in engines_list:
            engines_list.append(engine_name)
    return engines_list


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
        if item["language_id"] == language_code:
            return item["latitude"], item["longitude"], item["language"]
    return 0.0, 0.0, 'Unknown' # Default values if no match is found

def load_voices_from_source(engine: str):
    tts_engines_directory = os.path.realpath("./tts-data")
    voices = []
    geo_data = load_geo_data()  # Load geographical data

    # Load the specific engine's JSON file if it exists
    engine_file_path = os.path.join(tts_engines_directory, f"{engine}.json")
    if os.path.isfile(engine_file_path):
        with open(engine_file_path, 'r') as file:
            voices_raw = json.load(file)
            voices = [{"engine": engine, **item} for item in voices_raw]
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
    clients = {
        'polly': lambda: PollyClient(credentials=(
            os.getenv('POLLY_REGION'),
            os.getenv('POLLY_AWS_KEY_ID'),
            os.getenv('POLLY_AWS_ACCESS_KEY')
        )),
        'google': lambda: GoogleClient(credentials=(os.getenv('GOOGLE_CREDS_PATH'))),
        'microsoft': lambda: MicrosoftClient(credentials=(
            os.getenv('MICROSOFT_TOKEN'),
            os.getenv('MICROSOFT_REGION')
        )),
        'watson': lambda: WatsonClient(credentials=(
            os.getenv('WATSON_API_KEY'),
            os.getenv('WATSON_REGION'),
            os.getenv('WATSON_INSTANCE_ID')
        )),
        'elevenlabs': lambda: ElevenLabsClient(credentials=(os.getenv('ELEVENLABS_API_KEY'))),
        'witai': lambda: WitAiClient(credentials=(os.getenv('WITAI_TOKEN'))),
        'sherpaonnx': lambda: SherpaOnnxClient(),
        'playht': lambda: PlayHTClient(credentials=(
            os.getenv('PLAYHT_API_KEY'),
            os.getenv('PLAYHT_USER_ID')
        ))
    }
    client_func = clients.get(engine)
    if client_func is None:
        raise HTTPException(
            status_code=400, 
            detail=f"Engine '{engine}' not supported. Supported engines are: {list(clients.keys())}"
        )
    return client_func()

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
    elif engine == 'sherpaonnx':
        return SherpaOnnxTTS(client)
    elif engine == 'playht':
        return PlayHTTTS(client)
    elif engine == 'espeak':
        return eSpeakTTS(client)
    elif engine == 'avsynth':
        return AVSynthTTS(client)
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
        print(f"Fetching voices for engine as engine exists: {engine}")  
        if not ignore_cache:
            voices = get_cached_voices(engine.lower())
        if not voices:
            voices = load_voices_from_source(engine.lower())
            if not ignore_cache:
                cache_voices(engine.lower(), voices)
    else:
        for eng in engines_list:
            print(f"Fetching voices for engine: {eng}")
            if not ignore_cache:
                eng_voices = get_cached_voices(eng)
                if eng == 'SherpaOnnx':
                    print(f"Eng voices: {eng_voices}")
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

    # If page_size is 0, return all voices without pagination.
    if page_size == 0:
        paginated_voices = filtered_voices
    else:
        # Add type hints to fix pagination calculation errors
        start = (page - 1 if page else 0) * (page_size if page_size else 50)
        end = start + (page_size if page_size else 50)
        paginated_voices = filtered_voices[start:end]

    return [Voice(**voice) for voice in paginated_voices]

@app.get("/engines", response_model=List[str])
def get_available_engines():
    return engines_list

is_development = os.getenv('DEVELOPMENT') == 'True'
if is_development:
    logging.info("Loading credentials")
    from load_credentials import load_credentials
    load_credentials()


tts_engines_directory = os.path.realpath("./tts-data")
tts_engines = load_tts_engines(tts_engines_directory)
engines_list = update_engines_list(engines_list, tts_engines)

logger.info(f"Updated Engines List:{engines_list}")

for engine_name, engine_data in tts_engines.items():
    logger.info(f"Loaded TTS Engine: {engine_name} with data: {engine_data}")

if __name__ == "__main__":
    import uvicorn
    
    # Configure host and port
    host = "0.0.0.0"  # Allows external access
    port = 8000  # Default port for FastAPI
    
    # Run the server
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True  # Enable auto-reload on code changes
    )