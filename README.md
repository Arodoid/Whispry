# Voice Assistant Application

## Overview

This is a Windows application that runs in the background and activates a voice assistant when you press a specific key. The assistant listens to your inquiry, processes it using the Whisper API for transcription and GPT-4 for response generation, then speaks back the answer and optionally displays it in a popup.

## Features

- Press a designated key to start/stop recording.
- Use Whisper API to convert speech to text.
- Use GPT-4 API to generate a response.
- Speak the response aloud and display it in a popup.

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/voice_assistant.git
   cd voice_assistant
   ```

2. **Install required libraries**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Replace API Keys**:
   - Replace `'YOUR_OPENAI_API_KEY'` in `config/settings.py` with your actual OpenAI API key.

## Usage

1. **Run the application**:

   ```bash
   python app.py
   ```

2. **Press F9 to start recording**.
3. **Speak your inquiry**.
4. **Press F9 again to stop recording**.
5. **The assistant will process your request and respond**.

## Considerations

- Ensure your microphone is properly configured.
- Be mindful of OpenAI API usage rates and costs.
- Implement additional error handling for production use.
- To run the application on startup and minimize it, consider packaging it with `pyinstaller` as a Windows executable.
