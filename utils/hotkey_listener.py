from pynput import keyboard
from utils.audio_processing import start_recording, stop_recording, play_sound
from utils.gpt_response import get_response
from utils.text_to_speech import text_to_speech, stop_text_to_speech, is_audio_playing
import threading
import asyncio
import pyperclip
import logging
import os
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

recording_flags = {
    'hotkey1': False,
    'hotkey2': False,
    'hotkey3': False  # Added hotkey3
}
recording_locks = {
    'hotkey1': threading.Lock(),
    'hotkey2': threading.Lock(),
    'hotkey3': threading.Lock()  # Added lock for hotkey3
}

# Add a debounce time in seconds
DEBOUNCE_TIME = 0.2
last_toggle_time = {
    'hotkey1': 0,
    'hotkey2': 0,
    'hotkey3': 0  # Added hotkey3
}

# Locks for each hotkey to ensure thread safety
hotkey_locks = {
    'hotkey1': threading.Lock(),
    'hotkey2': threading.Lock(),
    'hotkey3': threading.Lock()  # Added hotkey3
}

def on_hotkey_pressed(hotkey_id, model, output_method, precontext, mode):
    current_time = time.time()

    with hotkey_locks[hotkey_id]:
        # Check for debounce only in Toggle mode
        if mode == 'Toggle' and current_time - last_toggle_time[hotkey_id] < DEBOUNCE_TIME:
            logging.info(f"Debounce active for '{hotkey_id}'. Ignoring toggle.")
            return

        last_toggle_time[hotkey_id] = current_time

        with recording_locks[hotkey_id]:
            # Check if any other hotkey is active
            if any(flag for key, flag in recording_flags.items() if key != hotkey_id and flag) and not recording_flags[hotkey_id]:
                logging.warning(f"Another hotkey is already active. Cannot start '{hotkey_id}'.")
                return

            # Toggle the recording state
            if not recording_flags[hotkey_id]:
                logging.info(f"Hotkey '{hotkey_id}' pressed: Initiating start sequence.")
                stop_text_to_speech()
                logging.info("Stopped any ongoing text-to-speech playback.")
                start_recording()
                logging.info("Recording started.")
                recording_flags[hotkey_id] = True
            else:
                logging.info(f"Hotkey '{hotkey_id}' pressed: Initiating stop sequence.")
                # Add a delay before stopping the recording
                time.sleep(0.5)  # 500ms delay, adjust as needed
                audio_file_path = stop_recording()
                logging.info(f"Recording stopped after delay. Audio file saved to {audio_file_path}")
                recording_flags[hotkey_id] = False
                if audio_file_path:
                    threading.Thread(
                        target=process_audio,
                        args=(audio_file_path, model, output_method, precontext),
                        daemon=True
                    ).start()
                    logging.info("Started processing audio in a new thread.")
                else:
                    logging.error("No audio file was created. Skipping audio processing.")

def process_audio(file_path, model, output_method, precontext):
    logging.info(f"Beginning to process audio file: {file_path}")
    from utils.transcription import transcribe_audio
    try:
        transcription = transcribe_audio(file_path)
        logging.info(f"Transcription: {transcription}")
        os.remove(file_path)  # Clean up the audio file after transcription
        logging.info(f"Deleted temporary audio file: {file_path}")

        if output_method == 'Clipboard':
            pyperclip.copy(transcription)
            logging.info("Transcription copied to clipboard.")
            play_sound('audio/clipboard_sound.mp3')
        else:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            logging.info(f"Sending transcription to GPT model '{model}' with precontext.")
            answer = loop.run_until_complete(get_response(transcription, model, output_method, precontext))
            logging.info(f"GPT Response: {answer}")

            if output_method == 'LLM':
                text_to_speech(answer)
            else:
                logging.warning(f"Unknown output method: {output_method}")
    except Exception as e:
        logging.error(f"Error processing audio: {e}")

def setup_hotkey_listener(hotkey_id, hotkey, mode, model, output_method, precontext):
    key_combination = {hotkey.lower()}  # Ensure the hotkey is in a set for comparison

    pressed_keys = set()
    key_pressed = False  # Track if the key is currently pressed

    def on_press(key):
        nonlocal key_pressed
        try:
            key_char = key.char.lower()
        except AttributeError:
            key_char = key.name.lower()

        # Stop audio playback when any key is pressed, but only if audio is playing
        if is_audio_playing():
            stop_text_to_speech()

        if key_char in key_combination:
            if not key_pressed:  # Only toggle if the key wasn't already pressed
                key_pressed = True
                logging.info(f"Hotkey '{hotkey_id}' detected: {key_combination}")
                if mode == 'Toggle':
                    on_hotkey_pressed(hotkey_id, model, output_method, precontext, mode)
                elif mode == 'Hold' and not recording_flags[hotkey_id]:
                    on_hotkey_pressed(hotkey_id, model, output_method, precontext, mode)

    def on_release(key):
        nonlocal key_pressed
        try:
            key_char = key.char.lower()
        except AttributeError:
            key_char = key.name.lower()

        if key_char in key_combination:
            key_pressed = False  # Reset the key pressed state

        if mode == 'Hold' and not key_combination <= pressed_keys and recording_flags[hotkey_id]:
            on_hotkey_pressed(hotkey_id, model, output_method, precontext, mode)

    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()
    return listener