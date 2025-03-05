import os
import json
from cryptography.fernet import Fernet
import sys
import logging


def encrypt_config(output_path, encryption_key):
    """
    Encrypt the configuration and save to the specified output path.
    """
    config = {
        "MICROSOFT_TOKEN": os.getenv("MICROSOFT_TOKEN"),
        "MICROSOFT_REGION": os.getenv("MICROSOFT_REGION"),
        "GOOGLE_CREDS_PATH": os.getenv("GOOGLE_CREDS_PATH"),
        "MICROSOFT_TOKEN_TRANS": os.getenv("MICROSOFT_TOKEN_TRANS"),
        "GOOGLE_CREDS_JSON": os.getenv("GOOGLE_CREDS_JSON"),
    }

    # Validate all config values are present
    missing = [k for k, v in config.items() if not v]
    if missing:
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")

    # Serialize to JSON
    config_json = json.dumps(config).encode()

    # Encrypt
    fernet = Fernet(encryption_key.encode())
    encrypted_config = fernet.encrypt(config_json)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write encrypted config
    with open(output_path, "wb") as f:
        f.write(encrypted_config)

    logging.info(f"Encrypted configuration saved to {output_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        encryption_key = os.getenv("CONFIG_ENCRYPTION_KEY")
        if not encryption_key:
            raise EnvironmentError(
                "CONFIG_ENCRYPTION_KEY environment variable is not set."
            )

        output_path = os.path.join(os.path.dirname(__file__), "config.enc")
        encrypt_config(output_path, encryption_key)
    except Exception as e:
        logging.error(f"Encryption failed: {e}")
        sys.exit(1)
