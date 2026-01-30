from abc import ABC, abstractmethod
import numpy as np

class ASRModel(ABC):
    @abstractmethod
    def load(self):
        """Load the model resources."""
        pass

    @abstractmethod
    def transcribe(self, audio_data: np.ndarray) -> str:
        """
        Transcribe the given audio data.
        
        Args:
            audio_data: 1D numpy array of float32 audio samples (sampled at 16kHz).
            
        Returns:
            The transcribed text as a string.
        """
        pass
    
    @abstractmethod
    def get_settings(self) -> dict:
        """Return current model settings/status."""
        pass
