# TTSVoicesAvailable

 Simple API to find any TTS voices available including offline Voices

Also a streamlit app to demo this. 

Note: tts-data/**vendor**-**software**.json is a list of tts engines not supported by tts-wrapper. Add to that if you wish

To-Do

- Add software specific variants like Smartbox
- Add in eSpeak-NG
- Investigate NVDA at some point
- Add in preview to the Voice class and a way of adding previews in the JSON

see docs at https://ttsvoices.acecentre.net/docs 

**NB: In requirements we are using our github versions of tts-wrapper. This breaks!**

## Random TTS engines not supported by wrapper

Some engines are not supported by tts-wrapper. As such we have to dump our own JSON files with their details in this repo. 

- Acapela is scraped using previews/get_acapela.py
- A random selection of others are in misc-misc.json
- We could do with rethinking this part. Its not fun adding more or keeping this up-to-date 

