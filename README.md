# Voice Assistant Application

This is a Python-based voice assistant application that allows users to interact with an AI model using hotkeys. The application supports audio transcription, text-to-speech, and integration with OpenAI's GPT models.

## Features

- **Hotkey Activation**: Configure up to three hotkeys to start and stop audio recording.
- **Audio Transcription**: Transcribe audio using OpenAI's Whisper model.
- **AI Response**: Get responses from OpenAI's GPT models.
- **Text-to-Speech**: Convert AI responses to speech using Google Cloud's Text-to-Speech API.
- **Clipboard Integration**: Copy transcriptions or AI responses to the clipboard.

## Requirements

- Python 3.7 or higher
- Virtual environment (recommended)
- Google Cloud Text-to-Speech API credentials
- OpenAI API key

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/yourusername/voice-assistant.git
   cd voice-assistant
   ```

2. **Set Up a Virtual Environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the Virtual Environment**:
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure API Keys**:
   - Create a `config/settings.py` file with the following content:
     ```python
     OPENAI_API_KEY = 'your-openai-api-key'
     ```
   - Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of your Google Cloud service account key file:
     ```bash
     export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-file.json"
     ```

6. **Run the Application**:
   ```bash
   python app.py
   ```

## Usage

- Launch the application and configure your audio input/output devices.
- Set up hotkeys for different actions.
- Use the hotkeys to start and stop audio recording.
- The application will transcribe the audio and provide AI responses based on your configuration.

## Troubleshooting

- Ensure all dependencies are installed correctly.
- Check the `voice_assistant.log` file for any error messages.
- Verify that your API keys and credentials are set up correctly.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
