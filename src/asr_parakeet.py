import os
import logging
import numpy as np
import sherpa_onnx
from huggingface_hub import snapshot_download
from asr_interface import ASRModel
from config_manager import settings

class ASRParakeet(ASRModel):
    def __init__(self):
        self.recognizer = None
        self.model_path = None
        
    def _download_model_if_needed(self):
        repo_id = settings.get("parakeet_model_repo", "csukuangfj/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8")
        cache_dir = os.path.expanduser("~/.cache/uwhisper/parakeet_model")
        
        # Check if files exist (basic check)
        expected_files = ["encoder.int8.onnx", "decoder.int8.onnx", "joiner.int8.onnx", "tokens.txt"]
        all_exist = all(os.path.exists(os.path.join(cache_dir, f)) for f in expected_files)
        
        if not all_exist:
            logging.info(f"Downloading Parakeet model from {repo_id}...")
            try:
                # We download to a specific folder to make it easy to find
                snapshot_download(repo_id=repo_id, local_dir=cache_dir, local_dir_use_symlinks=False)
                logging.info("Download complete.")
            except Exception as e:
                logging.error(f"Failed to download Parakeet model: {e}")
                raise
        
        self.model_path = cache_dir
        return cache_dir

    def load(self):
        if self.recognizer:
            return

        model_dir = self._download_model_if_needed()
        logging.info(f"Loading Parakeet model from {model_dir}...")
        
        logging.info(f"Loading Parakeet model from {model_dir}...")
        
        try:
            # Use the helper method from_transducer to avoid complex config construction
            # and ensure compatibility with installed sherpa-onnx version.
            # Now that metadata (vocab_size, context_size) is fixed in the files, this should work.
            self.recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
                tokens=os.path.join(model_dir, "tokens.txt"),
                encoder=os.path.join(model_dir, "encoder.int8.onnx"),
                decoder=os.path.join(model_dir, "decoder.int8.onnx"),
                joiner=os.path.join(model_dir, "joiner.int8.onnx"),
                num_threads=4,
                sample_rate=16000,
                feature_dim=128, # Correct dim for Parakeet TDT
                decoding_method="greedy_search",
                provider="cpu",
                model_type="nemo_transducer"
            )

            logging.info("Parakeet model loaded successfully.")

            logging.info("Parakeet model loaded successfully.")
        except Exception as e:
            logging.error(f"Error loading Parakeet model: {e}")
            raise

    def transcribe(self, audio_data: np.ndarray) -> str:
        if not self.recognizer:
            self.load()
            
        try:
             # audio_data is float32 [-1, 1], samples (N,)
             # sherpa-onnx OfflineRecognizer create_stream() takes None
             stream = self.recognizer.create_stream()
             
             # accept_waveform expects (sample_rate, waveform_tensor)
             # but python binding: stream.accept_waveform(sample_rate, samples)
             # samples should be float array
             stream.accept_waveform(16000, audio_data)
             
             self.recognizer.decode_stream(stream)
             result = stream.result
             return result.text.strip()

        except Exception as e:
            logging.error(f"Parakeet transcription error: {e}")
            raise

    def get_settings(self) -> dict:
        return {
            "type": "parakeet_tdt",
            "model_path": self.model_path
        }
