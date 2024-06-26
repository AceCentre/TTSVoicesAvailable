# use it like this
# jq -c '@json' ttsandtranslate-7dd2e2d80d42.json

import os

filename = os.getenv("GOOGLE_CREDS_PATH")

def create_google_creds_file():
    google_creds_json = os.getenv("GOOGLE_CREDS_JSON")
    if not google_creds_json:
        raise ValueError("GOOGLE_CREDS_JSON environment variable is not set")
    
    with open(filename, "w") as f:
        f.write(google_creds_json)

if __name__ == "__main__":
    create_google_creds_file()
