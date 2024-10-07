import logging
import tkinter as tk
from tkinter import messagebox, ttk
from utils.hotkey_listener import setup_hotkey_listener
from utils.audio_processing import get_audio_devices, set_audio_devices, get_default_device
from utils.text_to_speech import is_audio_playing, wait_for_audio_to_finish
from utils.config_manager import load_settings, save_settings
import threading
import pystray
from pystray import MenuItem as item
from PIL import Image
import sys
import os
import keyboard
import time
import sounddevice as sd

class VoiceAssistantApp:
    def __init__(self, root):
        logging.basicConfig(
            filename='voice_assistant.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        self.root = root
        self.root.title("Voice Assistant Configuration")
        self.root.geometry("500x650")  # Increased size to accommodate third hotkey
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.settings = load_settings()

        default_input_device = get_default_device('input')
        if default_input_device is None:
            self.logger.error("No default input device found.")
            messagebox.showerror(
                "No Input Device",
                "No default input audio device found.\nPlease select an input device in the settings."
            )

        default_output_device = get_default_device('output')
        if default_output_device is None:
            self.logger.error("No default output device found.")
            messagebox.showerror(
                "No Output Device",
                "No default output audio device found.\nPlease select an output device in the settings."
            )

        self.input_device_var = tk.StringVar(
            value=self.settings.get('input_device', default_input_device)
        )
        self.output_device_var = tk.StringVar(
            value=self.settings.get('output_device', default_output_device)
        )
        
        # Hotkey 1 Variables
        self.hotkey1_var = tk.StringVar(value=self.settings.get('hotkey1', 'F9'))
        self.hotkey1_mode_var = tk.StringVar(value=self.settings.get('hotkey1_mode', 'Hold'))
        self.hotkey1_model_var = tk.StringVar(value=self.settings.get('hotkey1_model', 'gpt-4o'))
        self.hotkey1_output_var = tk.StringVar(value=self.settings.get('hotkey1_output', 'LLM'))
        self.hotkey1_precontext_var = tk.StringVar(value=self.settings.get('hotkey1_precontext', 'Provide a concise and helpful response.'))

        # Hotkey 2 Variables
        self.hotkey2_var = tk.StringVar(value=self.settings.get('hotkey2', 'F10'))
        self.hotkey2_mode_var = tk.StringVar(value=self.settings.get('hotkey2_mode', 'Toggle'))
        self.hotkey2_model_var = tk.StringVar(value=self.settings.get('hotkey2_model', 'gpt-4o'))
        self.hotkey2_output_var = tk.StringVar(value=self.settings.get('hotkey2_output', 'Clipboard'))
        self.hotkey2_precontext_var = tk.StringVar(value=self.settings.get('hotkey2_precontext', 'Provide a concise and helpful response.'))

        # Hotkey 3 Variables
        self.hotkey3_var = tk.StringVar(value=self.settings.get('hotkey3', 'F11'))
        self.hotkey3_mode_var = tk.StringVar(value=self.settings.get('hotkey3_mode', 'Toggle'))
        self.hotkey3_model_var = tk.StringVar(value=self.settings.get('hotkey3_model', 'gpt-4o'))
        self.hotkey3_output_var = tk.StringVar(value=self.settings.get('hotkey3_output', 'Clipboard'))
        self.hotkey3_precontext_var = tk.StringVar(value=self.settings.get('hotkey3_precontext', 'Provide a concise and helpful response for the third hotkey.'))

        self.is_running = False

        self.is_listening_for_hotkey1 = False
        self.is_listening_for_hotkey2 = False
        self.is_listening_for_hotkey3 = False  # Added flag for hotkey3

        self.create_widgets()

        self.icon = None

        self.listeners = []

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20 20 20 20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        devices_frame = ttk.LabelFrame(main_frame, text="Audio Devices", padding="10 10 10 10")
        devices_frame.pack(fill=tk.X, pady=10)

        ttk.Label(devices_frame, text="Input (Microphone) Device:").grid(row=0, column=0, sticky=tk.W, pady=5)
        input_devices = get_audio_devices(kind='input')
        self.input_device_menu = ttk.Combobox(
            devices_frame, 
            textvariable=self.input_device_var, 
            values=input_devices, 
            state='readonly',
            width=40
        )
        self.input_device_menu.grid(row=0, column=1, pady=5, padx=10)
        if input_devices and self.input_device_var.get() not in input_devices:
            self.input_device_menu.current(0)

        ttk.Label(devices_frame, text="Output (Speaker) Device:").grid(row=1, column=0, sticky=tk.W, pady=5)
        output_devices = get_audio_devices(kind='output')
        self.output_device_menu = ttk.Combobox(
            devices_frame, 
            textvariable=self.output_device_var, 
            values=output_devices, 
            state='readonly',
            width=40
        )
        self.output_device_menu.grid(row=1, column=1, pady=5, padx=10)
        if output_devices and self.output_device_var.get() not in output_devices:
            self.output_device_menu.current(0)

        hotkeys_frame = ttk.LabelFrame(main_frame, text="Hotkeys Configuration", padding="10 10 10 10")
        hotkeys_frame.pack(fill=tk.X, pady=10)

        # Hotkey 1 Configuration
        ttk.Label(hotkeys_frame, text="Hotkey 1:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.hotkey1_entry = ttk.Entry(hotkeys_frame, textvariable=self.hotkey1_var, width=20, state='readonly')
        self.hotkey1_entry.grid(row=0, column=1, pady=5, padx=5)
        self.set_hotkey1_button = ttk.Button(hotkeys_frame, text="Set Hotkey", command=self.listen_for_hotkey1)
        self.set_hotkey1_button.grid(row=0, column=2, pady=5, padx=5)
        self.hotkey1_mode_menu = ttk.Combobox(
            hotkeys_frame,
            textvariable=self.hotkey1_mode_var,
            values=['Hold', 'Toggle'],
            state='readonly',
            width=10
        )
        self.hotkey1_mode_menu.grid(row=0, column=3, pady=5, padx=5)

        ttk.Label(hotkeys_frame, text="AI Model:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.hotkey1_model_menu = ttk.Combobox(
            hotkeys_frame,
            textvariable=self.hotkey1_model_var,
            values=['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo'],
            state='readonly',
            width=20
        )
        self.hotkey1_model_menu.grid(row=1, column=1, pady=5, padx=5)

        ttk.Label(hotkeys_frame, text="Output Method:").grid(row=1, column=2, sticky=tk.W, pady=5)
        self.hotkey1_output_menu = ttk.Combobox(
            hotkeys_frame,
            textvariable=self.hotkey1_output_var,
            values=['LLM', 'Clipboard'],
            state='readonly',
            width=15
        )
        self.hotkey1_output_menu.grid(row=1, column=3, pady=5, padx=5)
        self.hotkey1_output_menu.bind("<<ComboboxSelected>>", lambda e: self.toggle_model_selection(self.hotkey1_output_var, self.hotkey1_model_menu, self.hotkey1_precontext_entry))

        ttk.Label(hotkeys_frame, text="Pre-context:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.hotkey1_precontext_entry = ttk.Entry(hotkeys_frame, textvariable=self.hotkey1_precontext_var, width=50)
        self.hotkey1_precontext_entry.grid(row=2, column=1, columnspan=3, pady=5, padx=5, sticky=tk.W)

        ttk.Separator(hotkeys_frame, orient='horizontal').grid(row=3, column=0, columnspan=4, sticky='ew', pady=10)

        # Hotkey 2 Configuration
        ttk.Label(hotkeys_frame, text="Hotkey 2:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.hotkey2_entry = ttk.Entry(hotkeys_frame, textvariable=self.hotkey2_var, width=20, state='readonly')
        self.hotkey2_entry.grid(row=4, column=1, pady=5, padx=5)
        self.set_hotkey2_button = ttk.Button(hotkeys_frame, text="Set Hotkey", command=self.listen_for_hotkey2)
        self.set_hotkey2_button.grid(row=4, column=2, pady=5, padx=5)
        self.hotkey2_mode_menu = ttk.Combobox(
            hotkeys_frame,
            textvariable=self.hotkey2_mode_var,
            values=['Hold', 'Toggle'],
            state='readonly',
            width=10
        )
        self.hotkey2_mode_menu.grid(row=4, column=3, pady=5, padx=5)

        ttk.Label(hotkeys_frame, text="AI Model:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.hotkey2_model_menu = ttk.Combobox(
            hotkeys_frame,
            textvariable=self.hotkey2_model_var,
            values=['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo'],
            state='readonly',
            width=20
        )
        self.hotkey2_model_menu.grid(row=5, column=1, pady=5, padx=5)

        ttk.Label(hotkeys_frame, text="Output Method:").grid(row=5, column=2, sticky=tk.W, pady=5)
        self.hotkey2_output_menu = ttk.Combobox(
            hotkeys_frame,
            textvariable=self.hotkey2_output_var,
            values=['LLM', 'Clipboard'],
            state='readonly',
            width=15
        )
        self.hotkey2_output_menu.grid(row=5, column=3, pady=5, padx=5)
        self.hotkey2_output_menu.bind("<<ComboboxSelected>>", lambda e: self.toggle_model_selection(self.hotkey2_output_var, self.hotkey2_model_menu, self.hotkey2_precontext_entry))

        ttk.Label(hotkeys_frame, text="Pre-context:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.hotkey2_precontext_entry = ttk.Entry(hotkeys_frame, textvariable=self.hotkey2_precontext_var, width=50)
        self.hotkey2_precontext_entry.grid(row=6, column=1, columnspan=3, pady=5, padx=5, sticky=tk.W)

        ttk.Separator(hotkeys_frame, orient='horizontal').grid(row=7, column=0, columnspan=4, sticky='ew', pady=10)

        # Hotkey 3 Configuration
        ttk.Label(hotkeys_frame, text="Hotkey 3:").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.hotkey3_entry = ttk.Entry(hotkeys_frame, textvariable=self.hotkey3_var, width=20, state='readonly')
        self.hotkey3_entry.grid(row=8, column=1, pady=5, padx=5)
        self.set_hotkey3_button = ttk.Button(hotkeys_frame, text="Set Hotkey", command=self.listen_for_hotkey3)
        self.set_hotkey3_button.grid(row=8, column=2, pady=5, padx=5)
        self.hotkey3_mode_menu = ttk.Combobox(
            hotkeys_frame,
            textvariable=self.hotkey3_mode_var,
            values=['Hold', 'Toggle'],
            state='readonly',
            width=10
        )
        self.hotkey3_mode_menu.grid(row=8, column=3, pady=5, padx=5)

        ttk.Label(hotkeys_frame, text="AI Model:").grid(row=9, column=0, sticky=tk.W, pady=5)
        self.hotkey3_model_menu = ttk.Combobox(
            hotkeys_frame,
            textvariable=self.hotkey3_model_var,
            values=['gpt-4o-mini', 'gpt-4o', 'gpt-4-turbo'],
            state='readonly',
            width=20
        )
        self.hotkey3_model_menu.grid(row=9, column=1, pady=5, padx=5)

        ttk.Label(hotkeys_frame, text="Output Method:").grid(row=9, column=2, sticky=tk.W, pady=5)
        self.hotkey3_output_menu = ttk.Combobox(
            hotkeys_frame,
            textvariable=self.hotkey3_output_var,
            values=['LLM', 'Clipboard'],
            state='readonly',
            width=15
        )
        self.hotkey3_output_menu.grid(row=9, column=3, pady=5, padx=5)
        self.hotkey3_output_menu.bind("<<ComboboxSelected>>", lambda e: self.toggle_model_selection(self.hotkey3_output_var, self.hotkey3_model_menu, self.hotkey3_precontext_entry))

        ttk.Label(hotkeys_frame, text="Pre-context:").grid(row=10, column=0, sticky=tk.W, pady=5)
        self.hotkey3_precontext_entry = ttk.Entry(hotkeys_frame, textvariable=self.hotkey3_precontext_var, width=50)
        self.hotkey3_precontext_entry.grid(row=10, column=1, columnspan=3, pady=5, padx=5, sticky=tk.W)

        self.start_button = ttk.Button(main_frame, text="Start Assistant", command=self.toggle_assistant, width=30)
        self.start_button.pack(pady=20)

    def toggle_model_selection(self, output_var, model_menu, precontext_widget):
        if output_var.get() == 'Clipboard':
            model_menu.config(state='disabled')
            precontext_widget.config(state='disabled')
        else:
            model_menu.config(state='readonly')
            precontext_widget.config(state='normal')

    def listen_for_hotkey1(self):
        if not self.is_listening_for_hotkey1:
            self.is_listening_for_hotkey1 = True
            self.set_hotkey1_button.config(text="Press a key...")
            threading.Thread(target=self.wait_for_hotkey1).start()

    def listen_for_hotkey2(self):
        if not self.is_listening_for_hotkey2:
            self.is_listening_for_hotkey2 = True
            self.set_hotkey2_button.config(text="Press a key...")
            threading.Thread(target=self.wait_for_hotkey2).start()

    def listen_for_hotkey3(self):
        if not self.is_listening_for_hotkey3:
            self.is_listening_for_hotkey3 = True
            self.set_hotkey3_button.config(text="Press a key...")
            threading.Thread(target=self.wait_for_hotkey3).start()

    def wait_for_hotkey1(self):
        try:
            event = keyboard.read_event(suppress=True)
            while True:
                if event.event_type == keyboard.KEY_DOWN:
                    hotkey = event.name
                    break
                event = keyboard.read_event(suppress=True)
            self.root.after(0, self.set_hotkey1, hotkey)
        except Exception as e:
            logging.error(f"Error listening for hotkey1: {e}")
            self.root.after(0, self.reset_hotkey1_button)

    def wait_for_hotkey2(self):
        try:
            event = keyboard.read_event(suppress=True)
            while True:
                if event.event_type == keyboard.KEY_DOWN:
                    hotkey = event.name
                    break
                event = keyboard.read_event(suppress=True)
            self.root.after(0, self.set_hotkey2, hotkey)
        except Exception as e:
            logging.error(f"Error listening for hotkey2: {e}")
            self.root.after(0, self.reset_hotkey2_button)

    def wait_for_hotkey3(self):
        try:
            event = keyboard.read_event(suppress=True)
            while True:
                if event.event_type == keyboard.KEY_DOWN:
                    hotkey = event.name
                    break
                event = keyboard.read_event(suppress=True)
            self.root.after(0, self.set_hotkey3, hotkey)
        except Exception as e:
            logging.error(f"Error listening for hotkey3: {e}")
            self.root.after(0, self.reset_hotkey3_button)

    def set_hotkey1(self, hotkey):
        self.hotkey1_var.set(hotkey)
        self.is_listening_for_hotkey1 = False
        self.set_hotkey1_button.config(text="Set Hotkey")

    def set_hotkey2(self, hotkey):
        self.hotkey2_var.set(hotkey)
        self.is_listening_for_hotkey2 = False
        self.set_hotkey2_button.config(text="Set Hotkey")

    def set_hotkey3(self, hotkey):
        self.hotkey3_var.set(hotkey)
        self.is_listening_for_hotkey3 = False
        self.set_hotkey3_button.config(text="Set Hotkey")

    def reset_hotkey1_button(self):
        self.is_listening_for_hotkey1 = False
        self.set_hotkey1_button.config(text="Set Hotkey")

    def reset_hotkey2_button(self):
        self.is_listening_for_hotkey2 = False
        self.set_hotkey2_button.config(text="Set Hotkey")

    def reset_hotkey3_button(self):
        self.is_listening_for_hotkey3 = False
        self.set_hotkey3_button.config(text="Set Hotkey")

    def toggle_assistant(self):
        if not self.is_running:
            self.start_assistant()
        else:
            self.stop_assistant()

    def start_assistant(self):
        input_device = self.input_device_var.get()
        output_device = self.output_device_var.get()
        
        # Hotkey 1 Settings
        hotkey1 = self.hotkey1_var.get().strip()
        hotkey1_mode = self.hotkey1_mode_var.get().strip()
        hotkey1_model = self.hotkey1_model_var.get().strip() if self.hotkey1_output_var.get() != 'Clipboard' else None
        hotkey1_output = self.hotkey1_output_var.get().strip()
        hotkey1_precontext = self.hotkey1_precontext_var.get().strip()

        # Hotkey 2 Settings
        hotkey2 = self.hotkey2_var.get().strip()
        hotkey2_mode = self.hotkey2_mode_var.get().strip()
        hotkey2_model = self.hotkey2_model_var.get().strip() if self.hotkey2_output_var.get() != 'Clipboard' else None
        hotkey2_output = self.hotkey2_output_var.get().strip()
        hotkey2_precontext = self.hotkey2_precontext_var.get().strip()

        # Hotkey 3 Settings
        hotkey3 = self.hotkey3_var.get().strip()
        hotkey3_mode = self.hotkey3_mode_var.get().strip()
        hotkey3_model = self.hotkey3_model_var.get().strip() if self.hotkey3_output_var.get() != 'Clipboard' else None
        hotkey3_output = self.hotkey3_output_var.get().strip()
        hotkey3_precontext = self.hotkey3_precontext_var.get().strip()

        if not input_device or not output_device or not hotkey1 or not hotkey2 or not hotkey3:
            self.logger.warning("User attempted to start without selecting all settings.")
            messagebox.showwarning("Input Required", "Please select all settings before starting.")
            return

        set_audio_devices(input_device, output_device)
        # Save Hotkey 1 Settings
        self.settings['hotkey1'] = hotkey1
        self.settings['hotkey1_mode'] = hotkey1_mode
        self.settings['hotkey1_model'] = hotkey1_model
        self.settings['hotkey1_output'] = hotkey1_output
        self.settings['hotkey1_precontext'] = hotkey1_precontext

        # Save Hotkey 2 Settings
        self.settings['hotkey2'] = hotkey2
        self.settings['hotkey2_mode'] = hotkey2_mode
        self.settings['hotkey2_model'] = hotkey2_model
        self.settings['hotkey2_output'] = hotkey2_output
        self.settings['hotkey2_precontext'] = hotkey2_precontext

        # Save Hotkey 3 Settings
        self.settings['hotkey3'] = hotkey3
        self.settings['hotkey3_mode'] = hotkey3_mode
        self.settings['hotkey3_model'] = hotkey3_model
        self.settings['hotkey3_output'] = hotkey3_output
        self.settings['hotkey3_precontext'] = hotkey3_precontext

        self.settings['input_device'] = input_device
        self.settings['output_device'] = output_device
        save_settings(self.settings)
        self.logger.info(f"Settings saved: Input Device - {input_device}, Output Device - {output_device}, "
                         f"Hotkey1 - {hotkey1} ({hotkey1_mode}), Model - {hotkey1_model}, Output - {hotkey1_output}, "
                         f"Hotkey2 - {hotkey2} ({hotkey2_mode}), Model - {hotkey2_model}, Output - {hotkey2_output}, "
                         f"Hotkey3 - {hotkey3} ({hotkey3_mode}), Model - {hotkey3_model}, Output - {hotkey3_output}")

        try:
            listener1 = setup_hotkey_listener('hotkey1', hotkey1, hotkey1_mode, hotkey1_model, hotkey1_output, hotkey1_precontext)
            self.listeners.append(listener1)
            self.logger.info("Hotkey1 listener started.")

            listener2 = setup_hotkey_listener('hotkey2', hotkey2, hotkey2_mode, hotkey2_model, hotkey2_output, hotkey2_precontext)
            self.listeners.append(listener2)
            self.logger.info("Hotkey2 listener started.")

            listener3 = setup_hotkey_listener('hotkey3', hotkey3, hotkey3_mode, hotkey3_model, hotkey3_output, hotkey3_precontext)
            self.listeners.append(listener3)
            self.logger.info("Hotkey3 listener started.")
        except Exception as e:
            self.logger.error(f"Error starting hotkey listeners: {e}")
            messagebox.showerror("Error", "Failed to start hotkey listeners.")
            return

        self.start_button.config(text="Stop Assistant")
        self.is_running = True
        self.logger.info("Assistant started. Entering keep_alive loop.")
        self.keep_alive()

    def stop_assistant(self):
        self.logger.info("Stopping assistant...")
        try:
            for listener in self.listeners:
                listener.stop()
                self.logger.info("Hotkey listener stopped.")
        except Exception as e:
            self.logger.error(f"Error stopping hotkey listeners: {e}")

        self.start_button.config(text="Start Assistant")
        self.is_running = False
        self.logger.info("Assistant stopped.")

    def hide_window_to_tray(self):
        self.root.withdraw()

    def show_window(self, icon, item):
        self.root.deiconify()

    def exit_app(self, icon, item):
        icon.stop()
        sys.exit()

    def on_close(self):
        self.hide_window_to_tray()
        self.logger.info("Application minimized to tray.")

    def keep_alive(self):
        if is_audio_playing():
            self.logger.info("Audio is still playing")
        self.root.after(1000, self.keep_alive)

    def on_closing(self):
        self.logger.info("Closing application...")
        wait_for_audio_to_finish()
        self.root.destroy()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    try:
        logging.info("Starting application...")
        root = tk.Tk()
        app = VoiceAssistantApp(root)
        root.protocol("WM_DELETE_WINDOW", app.on_close)
        
        logging.info("Entering main loop...")
        root.mainloop()
        logging.info("Main loop exited.")
    except KeyboardInterrupt:
        logging.info("Application interrupted by user.")
        sys.exit()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        logging.critical("APPLICATION HAS EXITED")

if __name__ == "__main__":
    main()