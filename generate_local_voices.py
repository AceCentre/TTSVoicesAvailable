from tts_wrapper import AVSynthTTS, AVSynthClient, eSpeakTTS, eSpeakClient
import json
import os
import platform

def generate_avsynth_voices():
    """Generate JSON file for AVSynth voices (Mac only)"""
    if platform.system() != 'Darwin':
        print("AVSynth is only available on macOS")
        return
    
    try:
        client = AVSynthClient()
        tts = AVSynthTTS(client)
        voices = tts.get_voices()
        
        # Ensure the tts-data directory exists
        os.makedirs('./tts-data', exist_ok=True)
        
        # Write to JSON file
        with open('./tts-data/avsynth.json', 'w', encoding='utf-8') as f:
            json.dump(voices, f, indent=2, ensure_ascii=False)
        print(f"Generated avsynth.json with {len(voices)} voices")
    except Exception as e:
        print(f"Error generating AVSynth voices: {e}")

def generate_espeak_voices():
    """Generate JSON file for eSpeak voices"""
    try:
        client = eSpeakClient()
        tts = eSpeakTTS(client)
        voices = tts.get_voices()
        
        # Ensure the tts-data directory exists
        os.makedirs('./tts-data', exist_ok=True)
        
        # Write to JSON file
        with open('./tts-data/espeak.json', 'w', encoding='utf-8') as f:
            json.dump(voices, f, indent=2, ensure_ascii=False)
        print(f"Generated espeak.json with {len(voices)} voices")
    except Exception as e:
        print(f"Error generating eSpeak voices: {e}")

if __name__ == "__main__":
    print("Generating voice JSON files...")
    
    # Generate AVSynth voices if on Mac
    if platform.system() == 'Darwin':
        print("Generating AVSynth voices...")
        generate_avsynth_voices()
    
    # Generate eSpeak voices
    print("Generating eSpeak voices...")
    generate_espeak_voices()
    
    print("Done!") 