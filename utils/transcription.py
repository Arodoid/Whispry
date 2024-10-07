import requests
from config.settings import OPENAI_API_KEY
import logging

def transcribe_audio(file_path):
    url = 'https://api.openai.com/v1/audio/transcriptions'
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
    }
    try:
        with open(file_path, 'rb') as audio_file:
            files = {'file': audio_file}
            data = {'model': 'whisper-1'}
            response = requests.post(url, headers=headers, files=files, data=data)
            response.raise_for_status()
            return response.json()['text']
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error occurred: {e}")
        logging.error(f"Response content: {response.content.decode()}")
        raise
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        raise