import streamlit as st
import pandas as pd
import pydeck as pdk
import requests
from geopy.geocoders import Nominatim

# Initialize geolocator
geolocator = Nominatim(user_agent="voice-availability-map")

# Function to get voices from API
def get_voices(engine=None, lang_code=None, software=None):
    params = {}
    if engine:
        params['engine'] = engine
    if lang_code:
        params['lang_code'] = lang_code
    if software:
        params['software'] = software
    response = requests.get("http://127.0.0.1:8000/voices", params=params)
    return response.json()

# Function to aggregate voices by language
def aggregate_voices_by_language(data):
    lang_voices_count = {}
    for voice in data:
        for lang_code in voice['language_codes']:
            if lang_code not in lang_voices_count:
                lang_voices_count[lang_code] = 0
            lang_voices_count[lang_code] += 1
    return lang_voices_count

# Function to get latitude and longitude based on language code
def get_coordinates(language):
    try:
        location = geolocator.geocode(language)
        if location:
            return location.latitude, location.longitude
    except Exception as e:
        st.error(f"Error getting coordinates for {language}: {e}")
    return 0, 0

# Streamlit app
st.title("Voice Availability Map")

# Fetch data from API
voices = get_voices()

# Aggregate data by language
lang_voices_count = aggregate_voices_by_language(voices)

# Create a dataframe for visualization
df = pd.DataFrame(lang_voices_count.items(), columns=['Language', 'Voices'])
df[['Latitude', 'Longitude']] = df['Language'].apply(lambda x: pd.Series(get_coordinates(x)))

# Interactive Map
st.write("## Voice Availability by Language")
view_state = pdk.ViewState(latitude=0, longitude=0, zoom=1)
layer = pdk.Layer(
    'ScatterplotLayer',
    data=df,
    get_position='[Longitude, Latitude]',
    get_radius='Voices * 50000',
    get_fill_color='[200, 30, 0, 160]',
    pickable=True
)
tool_tip = {"html": "Language: {Language}<br/>Voices: {Voices}", "style": {"color": "white"}}
map = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tool_tip)
st.pydeck_chart(map)

# Filter Form
st.write("## Filter Voices")
engines_list = ["All", "polly", "google", "microsoft", "watson", "elevenlabs", "witai", "mms", "other"]
engine = st.selectbox("Select Engine", options=engines_list)
language = st.selectbox("Select Language", options=['All'] + list(lang_voices_count.keys()))

filtered_voices = get_voices(engine=None if engine == "All" else engine, lang_code=None if language == "All" else language)

st.write(f"### {len(filtered_voices)} Voices Found")
st.json(filtered_voices)
