import sounddevice as sd
import queue
import wave
from config.settings import INPUT_DEVICE, OUTPUT_DEVICE
from utils.text_to_speech import text_to_speech
import os
import winsound
import numpy as np
import pyaudio
import logging
import threading
from pydub import AudioSegment
from pydub.playback import _play_with_simpleaudio
from playsound import playsound

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

q = queue.Queue()
recording = False
audio_stream = None

def get_audio_devices(kind='input'):
    devices = sd.query_devices()
    if kind == 'input':
        return [device['name'] for device in devices if device['max_input_channels'] > 0 and not device['name'].startswith('Disabled')]
    elif kind == 'output':
        return [device['name'] for device in devices if device['max_output_channels'] > 0 and not device['name'].startswith('Disabled')]
    return []

def set_audio_devices(input_device_name, output_device_name):
    global INPUT_DEVICE, OUTPUT_DEVICE
    devices = sd.query_devices()
    input_device = next(
        (i for i, d in enumerate(devices) if d['name'] == input_device_name and d['max_input_channels'] > 0),
        None
    )
    output_device = next(
        (i for i, d in enumerate(devices) if d['name'] == output_device_name and d['max_output_channels'] > 0),
        None
    )
    
    if input_device is not None:
        INPUT_DEVICE = input_device
    if output_device is not None:
        OUTPUT_DEVICE = output_device

def audio_callback(indata, frames, time, status):
    if status:
        logging.warning(f"Audio callback status: {status}")
    q.put(indata.copy())

def start_recording():
    global recording, audio_stream
    recording = True
    q.queue.clear()  # Clear the queue before starting recording
    try:
        audio_stream = sd.InputStream(
            callback=audio_callback, 
            device=INPUT_DEVICE, 
            channels=1, 
            samplerate=16000, 
            blocksize=8000
        )
        audio_stream.start()
        logging.info("Audio stream started successfully.")
    except Exception as e:
        logging.error(f"Error starting audio stream: {e}")
        recording = False
    play_sound(os.path.join('audio', 'start_sound.mp3'))  # Use MP3 file

def stop_recording():
    global recording, audio_stream
    recording = False
    if audio_stream:
        audio_stream.stop()
        audio_stream.close()
        logging.info("Audio stream stopped and closed.")
    else:
        logging.warning("Audio stream was not active.")
    play_sound(os.path.join('audio', 'stop_sound.mp3'))  # Use MP3 file
    return save_audio_file()

def save_audio_file():
    audio_frames = []
    while not q.empty():
        audio_frames.append(q.get())
    if not audio_frames:
        logging.warning("No audio data captured.")
        return None
    audio_data = (np.concatenate(audio_frames, axis=0) * 32767).astype(np.int16)
    
    file_path = 'audio/input.wav'
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    try:
        with wave.open(file_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(audio_data.tobytes())
        logging.info(f"Audio file saved at {file_path}")
    except Exception as e:
        logging.error(f"Error saving audio file: {e}")
        return None
    return file_path

def play_sound(sound_path):
    def play():
        logging.info(f"Attempting to play sound: {sound_path}")
        if not os.path.isfile(sound_path):
            logging.error(f"Sound file does not exist: {sound_path}")
            return
        try:
            playsound(sound_path)
            logging.info("Sound playback finished")
        except Exception as e:
            logging.error(f"Error playing sound: {e}")
    threading.Thread(target=play).start()

def get_default_device(kind='input'):
    p = pyaudio.PyAudio()
    try:
        if kind == 'input':
            device_info = p.get_default_input_device_info()
            device_name = device_info['name']
            logging.info(f"Default input device: {device_name}")
        elif kind == 'output':
            device_info = p.get_default_output_device_info()
            device_name = device_info['name']
            logging.info(f"Default output device: {device_name}")
        else:
            device_name = None
    except IOError as e:
        logging.error(f"Error getting default {kind} device: {e}")
        device_name = None
    finally:
        p.terminate()
    return device_name