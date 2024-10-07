from google.cloud import texttospeech
import os
import threading
import logging
import uuid
import time
from pydub import AudioSegment
from pydub.playback import play
from playsound import playsound
from pynput import keyboard
import wave
import pyaudio
import atexit

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

audio_playing = threading.Event()
audio_playing_lock = threading.Lock()
current_playback = None
current_audio_file = None

# List to store temporary files for later deletion
temp_files = []

def delete_temp_files():
    global temp_files
    for file in temp_files[:]:  # Iterate over a copy of the list
        try:
            if os.path.exists(file):
                os.close(os.open(file, os.O_RDONLY))  # Ensure the file is closed
                os.remove(file)
                logging.info(f"Deleted temporary audio file: {file}")
                temp_files.remove(file)
        except Exception as e:
            logging.error(f"Error deleting temporary file '{file}': {e}")
            # If we can't delete it now, we'll try again later
    
    # If there are still files to delete, schedule another attempt
    if temp_files:
        threading.Timer(5.0, delete_temp_files).start()

# Register the cleanup function to run at exit
atexit.register(delete_temp_files)

def text_to_speech(text):
    global current_playback, current_audio_file
    audio_filename = os.path.abspath(f"audio/response_{uuid.uuid4()}.wav")
    os.makedirs(os.path.dirname(audio_filename), exist_ok=True)
    
    # Add the filename to the list of temporary files
    temp_files.append(audio_filename)
    
    # Initialize Google Cloud TTS client
    client = texttospeech.TextToSpeechClient()
    
    # Set the text input to be synthesized
    synthesis_input = texttospeech.SynthesisInput(text=text)
    
    # Build the voice request
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    
    # Select the type of audio file you want returned
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.LINEAR16
    )
    
    # Perform the text-to-speech request
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    
    # Save the response to an audio file
    with open(audio_filename, "wb") as out:
        out.write(response.audio_content)
        logging.info(f'Audio content written to file "{audio_filename}"')

    def play_audio():
        global current_playback, current_audio_file
        try:
            logging.info(f"Playing sound: {audio_filename}")
            audio_playing.set()
            current_audio_file = audio_filename
            
            # Open the wave file
            with wave.open(audio_filename, 'rb') as wf:
                # Initialize PyAudio
                p = pyaudio.PyAudio()
                
                # Open a stream
                stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                                channels=wf.getnchannels(),
                                rate=wf.getframerate(),
                                output=True)
                
                # Read data in chunks
                chunk = 1024
                data = wf.readframes(chunk)
                
                # Play the sound
                while len(data) > 0 and audio_playing.is_set():
                    stream.write(data)
                    data = wf.readframes(chunk)
                
                # Clean up
                stream.stop_stream()
                stream.close()
                p.terminate()
            
        except Exception as e:
            logging.error(f"Error playing sound: {e}")
        finally:
            audio_playing.clear()
            current_playback = None
            current_audio_file = None
            logging.info("Playback finished")
            # Schedule file deletion
            threading.Timer(1.0, delete_temp_files).start()

    playback_thread = threading.Thread(target=play_audio)
    playback_thread.start()

def stop_text_to_speech():
    global current_playback, current_audio_file
    with audio_playing_lock:
        if audio_playing.is_set():
            logging.info("Stopping text-to-speech playback")
            audio_playing.clear()
            current_playback = None
            logging.info("Playback stopped")
    # Schedule file deletion
    threading.Timer(1.0, delete_temp_files).start()

def is_audio_playing():
    return audio_playing.is_set()

def wait_for_audio_to_finish():
    audio_playing.wait()