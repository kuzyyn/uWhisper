import logging
import numpy as np
from faster_whisper import WhisperModel
from asr_interface import ASRModel
from config_manager import settings

class ASRWhisper(ASRModel):
    def __init__(self):
        self.model = None
        self.current_model_size = None
        
    def load(self):
        desired_size = settings.get("model_size")
        device = settings.get("device")
        compute_type = settings.get("compute_type")

        # Skip if already loaded with same settings
        if self.model and self.current_model_size == desired_size:
            return

        logging.info(f"Loading Faster Whisper model ({desired_size}) on {device}...")
        
        try:
            self.model = WhisperModel(desired_size, device=device, compute_type=compute_type)
            self.current_model_size = desired_size
            logging.info("Faster Whisper model loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading Faster Whisper model: {e}")
            raise

    def transcribe(self, audio_data: np.ndarray) -> str:
        if not self.model:
            self.load()
            
        try:
            # Determine language
            lang = settings.get("language")
            if lang == "auto":
                lang = None
                
            segments, info = self.model.transcribe(audio_data, beam_size=5, language=lang)
            
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text)
            
            text = " ".join(text_parts).strip()
            return text
        except Exception as e:
            logging.error(f"Whisper transcription error: {e}")
            raise

    def get_settings(self) -> dict:
        return {
            "type": "faster_whisper",
            "model_size": self.current_model_size
        }
