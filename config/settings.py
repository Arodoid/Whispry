import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

# Default audio devices (will be populated by the application)
INPUT_DEVICE = None  # To be set by the user
OUTPUT_DEVICE = None  # To be set by the user