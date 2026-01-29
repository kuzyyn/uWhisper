import os
import logging
import socket
import threading
import queue
import time
import subprocess
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from config_manager import settings
from config import SOCKET_PATH
from signals import ServerSignals

class WhisperServer:
    def __init__(self):
        self.running = True
        self.recording = False
        self.audio_queue = queue.Queue()
        self.model = None
        self.samplerate = 16000
        self.abort_transcription = False
        
        # Signals for GUI
        self.signals = ServerSignals()
        
        # Current loaded model settings
        self.current_model_size = None
        self.current_language = None
        
        # Ensure socket cleanup
        socket_path = SOCKET_PATH
        if os.path.exists(socket_path):
            os.remove(socket_path)

    def load_model(self):
        desired_size = settings.get("model_size")
        device = settings.get("device")
        compute_type = settings.get("compute_type")

        # Skip if already loaded with same settings
        if self.model and self.current_model_size == desired_size:
            return

        logging.info(f"Loading Whisper model ({desired_size}) on {device}...")
        self.notify("System", f"Loading model ({desired_size})...")
        
        try:
            self.model = WhisperModel(desired_size, device=device, compute_type=compute_type)
            self.current_model_size = desired_size
            logging.info("Model loaded successfully.")
            self.notify("System", "Model loaded. Ready.")
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            self.notify("Error", f"Failed to load model: {e}")

    def notify(self, title, message):
        if settings.get("show_notifications", True):
            subprocess.run(['notify-send', "uWhisper", message])

    def copy_to_clipboard(self, text):
        try:
            process = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE)
            process.communicate(input=text.encode('utf-8'))
            logging.info(f"Copied to clipboard: {text}")
        except Exception as e:
            logging.error(f"Clipboard error: {e}")

    def audio_callback(self, indata, frames, time, status):
        # if status:
        #     print(f"Audio status: {status}")
        if self.recording:
            self.audio_queue.put(indata.copy())
            
            # Calculate Amplitude (RMS) for Visualization
            rms = np.sqrt(np.mean(indata**2))
            # Normalize reasonably (voice is usually low amplitude)
            # typical values 0.01 - 0.2, boost it for visuals
            level = min(rms * 10, 1.0)
            try:
                self.signals.amplitude_changed.emit(level)
            except RuntimeError:
                # App is shutting down, signal object deleted
                pass

    def get_downloaded_models(self):
        """Check standard HF cache for faster-whisper models"""
        try:
            cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
            if not os.path.exists(cache_dir):
                return []
            
            # Look for folders starting with "models--Systran--faster-whisper-"
            models = []
            prefix = "models--Systran--faster-whisper-"
            for name in os.listdir(cache_dir):
                if name.startswith(prefix):
                    model_name = name[len(prefix):]
                    models.append(model_name)
            return models
        except Exception as e:
            logging.error(f"Error listing models: {e}")
            return []

    def delete_model(self, model_size):
        """Delete a model from cache"""
        try:
            import shutil
            cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
            folder_name = f"models--Systran--faster-whisper-{model_size}"
            full_path = os.path.join(cache_dir, folder_name)
            
            if os.path.exists(full_path):
                shutil.rmtree(full_path)
                logging.info(f"Deleted model: {model_size}")
                return True
            return False
        except Exception as e:
            logging.error(f"Error deleting model: {e}")
            return False

    def download_model(self, model_size):
        """Download model in a blocking way (run in thread)"""
        try:
            logging.info(f"Downloading {model_size}...")
            # dry_run=False effectively downloads it
            # We just init the model path download utilizing the library
            from faster_whisper import download_model
            download_model(model_size)
            logging.info("Download complete.")
            return True
        except Exception as e:
            logging.error(f"Download error: {e}")
            return False

    def record_loop(self):
        with sd.InputStream(samplerate=self.samplerate, channels=1, callback=self.audio_callback):
            while self.running:
                time.sleep(0.1)

    def cancel_recording(self):
        logging.info("Cancellation requested.")
        self.recording = False
        self.abort_transcription = True
        # Clear queue
        with self.audio_queue.mutex:
            self.audio_queue.queue.clear()
        self.signals.state_changed.emit("idle")

    def process_audio(self):
        if self.abort_transcription:
            logging.info("Transcription aborted.")
            self.abort_transcription = False
            self.signals.state_changed.emit("idle")
            return

        self.signals.state_changed.emit("transcribing")
        
        audio_data = []
        while not self.audio_queue.empty():
            audio_data.append(self.audio_queue.get())
        
        if not audio_data:
            self.signals.state_changed.emit("idle")
            return

        audio_np = np.concatenate(audio_data, axis=0)
        audio_np = audio_np.flatten().astype(np.float32)

        logging.info("Transcribing...")
        self.load_model() # Check if model needs reloading
        
        try:
            # Determine language
            lang = settings.get("language")
            if lang == "auto":
                lang = None
                
            segments, info = self.model.transcribe(audio_np, beam_size=5, language=lang)
            
            text_parts = []
            for segment in segments:
                if self.abort_transcription:
                    logging.warning("Transcription aborted during segment processing.")
                    break
                text_parts.append(segment.text)
            
            if self.abort_transcription:
                self.abort_transcription = False
                self.signals.state_changed.emit("idle")
                return

            text = " ".join(text_parts).strip()
            
            if text:
                logging.info(f"Transcription: {text}")
                self.signals.text_ready.emit(text)
                self.copy_to_clipboard(text)
                
                # Check output mode
                mode = settings.get("output_mode")
                if mode == "paste":
                     # Simulate Paste
                     # Wait for overlay to disappear (it stays for 800ms)
                     time.sleep(1.0)
                     
                     paste_success = False

                     # Method 1: evdev (Native uinput)
                     try:
                         from evdev import UInput, ecodes
                         # Create a virtual keyboard
                         with UInput() as ui:
                             # Press Ctrl
                             ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 1)
                             # Press V
                             ui.write(ecodes.EV_KEY, ecodes.KEY_V, 1)
                             # Sync
                             ui.syn()
                             
                             time.sleep(0.05)
                             
                             # Release V
                             ui.write(ecodes.EV_KEY, ecodes.KEY_V, 0)
                             # Release Ctrl
                             ui.write(ecodes.EV_KEY, ecodes.KEY_LEFTCTRL, 0)
                             ui.syn()
                             
                         logging.info("Simulated Ctrl+V (evdev)")
                         paste_success = True
                     except ImportError:
                         logging.warning("evdev module not found.")
                     except Exception as e:
                         # print(f"evdev failed: {e}")
                         pass

                     if not paste_success:
                         self.notify("Paste Failed", "Input simulation failed. Check permissions.")
                         logging.error("All paste methods failed.")

                # self.notify("Transcription Complete", f"Copied: {text}")
            else:
                self.notify("Status", "No speech detected.")
                
        except Exception as e:
            logging.error(f"Transcription error: {e}")
            self.notify("Error", f"Transcription failed: {e}")
            
        self.signals.state_changed.emit("idle")

    def handle_client(self, conn):
        try:
            data = conn.recv(1024).decode().strip()
            if data == "TOGGLE":
                current_time = time.time()
                # 500ms debounce
                if hasattr(self, 'last_toggle_time') and (current_time - self.last_toggle_time < 0.5):
                    logging.debug("Debounced toggle request.")
                    return

                self.last_toggle_time = current_time

                if self.recording:
                    logging.info("Stopping recording...")
                    self.recording = False
                    # self.notify("uWhisper", "Processing...")
                    # Overlay handles "Processing" state
                    threading.Thread(target=self.process_audio).start()
                else:
                    logging.info("Starting recording...")
                    self.abort_transcription = False
                    with self.audio_queue.mutex:
                        self.audio_queue.queue.clear()
                    self.recording = True
                    self.signals.state_changed.emit("recording")
                    # self.notify("uWhisper", "Recording started...")
                    # Overlay handles "Recording" state
        except Exception as e:
            logging.error(f"Socket error: {e}")
        finally:
            conn.close()

    def start(self):
        # self.load_model() # Lazy load on first transcribe? Or preload?
        # Let's preload if configured, otherwise wait
        # self.load_model()
        
        threading.Thread(target=self.record_loop, daemon=True).start()

        socket_path = SOCKET_PATH
        server_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server_sock.bind(socket_path)
        server_sock.listen(1)
        
        # print(f"Listening on {socket_path}")
        
        try:
            while self.running:
                conn, _ = server_sock.accept()
                self.handle_client(conn)
        except Exception as e:
            logging.error(f"Server error: {e}")
        finally:
            self.running = False
            if os.path.exists(socket_path):
                os.remove(socket_path)
    
    def stop(self):
        self.running = False
