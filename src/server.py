import os
import logging
import socket
import threading
import queue
import time
import subprocess
import numpy as np
import sounddevice as sd
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
        
        self.headless = False

        
        # Ensure socket cleanup
        socket_path = SOCKET_PATH
        if os.path.exists(socket_path):
            os.remove(socket_path)

    def load_model(self):
        backend = settings.get("model_backend", "faster_whisper")
        
        # If model is loaded but backend changed, reset
        if self.model:
            current_settings = self.model.get_settings()
            if current_settings.get("type") != backend:
                logging.info(f"Switching backend from {current_settings.get('type')} to {backend}")
                self.model = None
            elif backend == "parakeet_tdt" and current_settings.get("variant") != settings.get("parakeet_variant"):
                 logging.info(f"Switching Parakeet variant from {current_settings.get('variant')} to {settings.get('parakeet_variant')}")
                 self.model = None

        if not self.model:
            logging.info(f"Initializing backend: {backend}")
            try:
                if backend == "faster_whisper":
                    from asr_whisper import ASRWhisper
                    self.model = ASRWhisper()
                elif backend == "parakeet_tdt":
                    from asr_parakeet import ASRParakeet
                    self.model = ASRParakeet()
                else:
                    logging.error(f"Unknown backend: {backend}")
                    self.notify("Error", f"Unknown backend: {backend}")
                    return
            except ImportError as e:
                logging.error(f"Failed to import backend {backend}: {e}")
                self.notify("Error", f"Missing dependencies for {backend}")
                return

        self.signals.state_changed.emit("loading")


        # Load the actual model resources (this might check for settings changes internally)
        try:
            self.model.load()
            self.signals.state_changed.emit("transcribing") # Restore state if we were processing
            # self.notify("System", "Model Ready") # Redundant if workflow is correct
        except Exception as e:

            logging.error(f"Error loading model: {e}")
            self.notify("Error", f"Model load failed: {e}")

    def notify(self, title, message):
        # Emit signal for GUI Overlay
        self.signals.notification.emit(title, message)
        
        # If headless, use system notifications (if enabled in settings/headless logic)
        # We assume headless mode wants notifications always or based on config
        if self.headless:
            subprocess.run(['notify-send', "uWhisper", f"{title}: {message}"])


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
        # TODO: Abstract this for other backends if needed
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
        backend = settings.get("model_backend", "faster_whisper")
        try:
            import shutil
            
            if backend == "faster_whisper":
                cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
                folder_name = f"models--Systran--faster-whisper-{model_size}"
                full_path = os.path.join(cache_dir, folder_name)
                
                if os.path.exists(full_path):
                    shutil.rmtree(full_path)
                    logging.info(f"Deleted model: {model_size}")
                    return True
            elif backend == "parakeet_tdt":
                # Shared folder for the configured repo
                cache_dir = os.path.expanduser("~/.cache/uwhisper/parakeet_model")
                if os.path.exists(cache_dir):
                    shutil.rmtree(cache_dir)
                    logging.info("Deleted Parakeet model cache.")
                    return True
                    
            return False
        except Exception as e:
            logging.error(f"Error deleting model: {e}")
            return False

    def download_model(self, model_size):
        """Download model in a blocking way (run in thread)"""
        backend = settings.get("model_backend", "faster_whisper")
        
        try:
            logging.info(f"Downloading {model_size} for {backend}...")
            
            if backend == "faster_whisper":
                from faster_whisper import download_model
                download_model(model_size)
            elif backend == "parakeet_tdt":
                # For Parakeet, 'load()' triggers the download of the configured repo
                from asr_parakeet import ASRParakeet
                # We instantiate and load. This might load into memory which is heavy 
                # just for a "download" button, but it ensures files are there.
                # A better way would be exposing only _download_model_if_needed 
                # but that is private. For now, full load is acceptable as verification.
                temp_model = ASRParakeet()
                temp_model.load() 
                
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
        
        self.load_model() # Check if model needs loading/reloading
        
        if not self.model:
             logging.error("No model available")
             self.signals.state_changed.emit("idle")
             return

        try:
            text = self.model.transcribe(audio_np)
            
            if self.abort_transcription:
                self.abort_transcription = False
                self.signals.state_changed.emit("idle")
                return

            if text:
                logging.info(f"Transcription: {text}")
                self.copy_to_clipboard(text)
                self.signals.text_ready.emit(text)
                
                # Check output mode
                mode = settings.get("output_mode")
                if mode == "paste":
                     # If headless, we need to handle paste here (blindly)
                     if self.headless:
                         from input_simulator import simulate_ctrl_v
                         time.sleep(0.5) # Slight safety delay for headless
                         if not simulate_ctrl_v():
                             self.notify("Paste Failed", "Input simulation failed.")
                     else:
                         # GUI mode: Let GUI handle the pasting after hiding overlay to manage focus
                         pass 

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
