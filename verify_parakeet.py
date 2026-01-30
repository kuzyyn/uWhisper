import sherpa_onnx
import os
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)

model_dir = os.path.expanduser("~/.cache/uwhisper/parakeet_model")
print(f"Loading from {model_dir}")

try:
    recognizer = sherpa_onnx.OfflineRecognizer.from_transducer(
        tokens=os.path.join(model_dir, "tokens.txt"),
        encoder=os.path.join(model_dir, "encoder.int8.onnx"),
        decoder=os.path.join(model_dir, "decoder.int8.onnx"),
        joiner=os.path.join(model_dir, "joiner.int8.onnx"),
        num_threads=4,
        sample_rate=16000,
        feature_dim=128,
        decoding_method="greedy_search",
        provider="cpu",
        model_type="nemo_transducer"
    )
    print("Model loaded successfully!")
    
    # Create dummy audio
    audio = np.zeros(16000, dtype=np.float32)
    stream = recognizer.create_stream()
    stream.accept_waveform(16000, audio)
    recognizer.decode_stream(stream)
    print("Decoding ran successfully (result might be empty string for silence).")
    print(f"Result: '{stream.result.text}'")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
