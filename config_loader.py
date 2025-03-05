import os
import json
from cryptography.fernet import Fernet
import logging


def load_config():
    """
    Load configuration from environment variables.
    If not present, load from an encrypted file.
    """
    config = {}

    # Attempt to load from environment variables
    config["MICROSOFT_TOKEN"] = os.getenv("MICROSOFT_TOKEN")
    config["MICROSOFT_REGION"] = os.getenv("MICROSOFT_REGION")
    config["GOOGLE_CREDS_PATH"] = os.getenv("GOOGLE_CREDS_PATH")
    config["MICROSOFT_TOKEN_TRANS"] = os.getenv("MICROSOFT_TOKEN_TRANS")

    # Check if all required environment variables are present
    if all(config.values()):
        logging.info("Loaded configuration from environment variables.")
        return config

    logging.info(
        "Environment variables incomplete or not set. Attempting to load from encrypted file."
    )

    # Fallback to encrypted config file
    encrypted_config_path = os.path.join(
        os.path.dirname(__file__), "_internal", "config.enc"
    )

    if not os.path.isfile(encrypted_config_path):
        raise FileNotFoundError(
            f"Encrypted configuration file not found at {encrypted_config_path}."
        )

    encryption_key = os.getenv("CONFIG_ENCRYPTION_KEY")
    if not encryption_key:
        raise EnvironmentError("CONFIG_ENCRYPTION_KEY environment variable is not set.")

    try:
        with open(encrypted_config_path, "rb") as f:
            encrypted_data = f.read()

        fernet = Fernet(encryption_key.encode())
        decrypted_data = fernet.decrypt(encrypted_data)
        config = json.loads(decrypted_data.decode())

        logging.info("Loaded configuration from encrypted file.")
        return config

    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        raise e


# Usage Example
if __name__ == "__main__":
    try:
        config = load_config()
        print("Configuration Loaded Successfully.")
        print(config)
    except Exception as error:
        print(f"Error loading configuration: {error}")
