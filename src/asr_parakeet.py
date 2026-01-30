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
        self.loaded_variant = None
        
    def _download_model_if_needed(self):
        variant = settings.get("parakeet_variant", "v2_en")
        
        if variant == "v3_multi":
            repo_id = "csukuangfj/sherpa-onnx-nemo-parakeet-tdt-0.6b-v3-int8"
            cache_dir = os.path.expanduser("~/.cache/uwhisper/parakeet_model_v3")
        else:
            # Default to v2_en
            repo_id = "csukuangfj/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"
            cache_dir = os.path.expanduser("~/.cache/uwhisper/parakeet_model")

        # Check if files exist (basic check)
        expected_files = ["encoder.int8.onnx", "decoder.int8.onnx", "joiner.int8.onnx", "tokens.txt"]
        all_exist = all(os.path.exists(os.path.join(cache_dir, f)) for f in expected_files)
        
        if not all_exist:
            logging.info(f"Downloading Parakeet model ({variant}) from {repo_id}...")
            try:
                # We download to a specific folder to make it easy to find
                snapshot_download(repo_id=repo_id, local_dir=cache_dir, local_dir_use_symlinks=False)
                logging.info("Download complete.")
                
                # Check and fix metadata (auto-apply fix if needed)
                self._ensure_metadata(cache_dir, variant)
                
            except Exception as e:
                logging.error(f"Failed to download Parakeet model: {e}")
                raise
        
        self.model_path = cache_dir
        self.loaded_variant = variant
        return cache_dir

    def _ensure_metadata(self, model_dir, variant):
        """
        Automatically fix metadata (vocab_size, context_size) if missing.
        This allows new downloads to work out-of-the-box without running external scripts.
        """
        import onnx
        
        def add_meta(path, key, value):
            try:
                model = onnx.load(path)
                exists = any(p.key == key for p in model.metadata_props)
                if not exists:
                    logging.info(f"Adding missing metadata {key}={value} to {path}")
                    meta = model.metadata_props.add()
                    meta.key = key
                    meta.value = str(value)
                    onnx.save(model, path)
            except Exception as e:
                logging.warning(f"Failed to update metadata for {path}: {e}")

        # Both V2 and V3 typically need this 
        # (V3 vocab size is 1025 too? We'll assume yes for now given it's TDT, 
        # but if V3 fails we might need to inspect tokens.txt)
        # However, for safety, let's read vocab size from tokens.txt
        try:
             with open(os.path.join(model_dir, "tokens.txt"), 'r', encoding='utf-8') as f:
                 lines = f.readlines()
                 vocab_size = len(lines)
        except:
             vocab_size = 1025 # Fallback
        
        decoder_path = os.path.join(model_dir, "decoder.int8.onnx")
        joiner_path = os.path.join(model_dir, "joiner.int8.onnx")
        
        if os.path.exists(decoder_path):
             add_meta(decoder_path, "vocab_size", vocab_size)
             add_meta(decoder_path, "context_size", 2)
        
        if os.path.exists(joiner_path):
             add_meta(joiner_path, "vocab_size", vocab_size)

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
            "model_path": self.model_path,
            "variant": self.loaded_variant
        }
