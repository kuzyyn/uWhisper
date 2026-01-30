import onnx
import os

model_dir = os.path.expanduser("~/.cache/uwhisper/parakeet_model")
decoder_path = os.path.join(model_dir, "decoder.int8.onnx")
joiner_path = os.path.join(model_dir, "joiner.int8.onnx")

def add_metadata(path, key, value):
    print(f"Processing {path}...")
    try:
        model = onnx.load(path)
        
        # Check if already exists
        exists = False
        for prop in model.metadata_props:
            if prop.key == key:
                print(f"  {key} already exists with value: {prop.value}")
                exists = True
                if prop.value != value:
                    print(f"  Updating to {value}...")
                    prop.value = value
                break
        
        if not exists:
            print(f"  Adding {key}={value}...")
            meta = model.metadata_props.add()
            meta.key = key
            meta.value = value
            
        onnx.save(model, path)
        print("  Saved.")
    except Exception as e:
        print(f"  Error: {e}")

# The error was in InitDecoder, so decoder needs it. 
# Usually tokens.txt has 1025 lines, so vocab_size is 1025.
# Let's count tokens just to be sure.
try:
    with open(os.path.join(model_dir, "tokens.txt"), "r", encoding="utf-8") as f:
        vocab_size = sum(1 for line in f)
    print(f"Detected vocab_size from tokens.txt: {vocab_size}")
except:
    vocab_size = 1025
    print(f"Could not read tokens.txt, assuming default: {vocab_size}")

add_metadata(decoder_path, "vocab_size", str(vocab_size))
add_metadata(decoder_path, "context_size", "2") # Typical for Parakeet/TDT

# InitJoiner might also need it?
add_metadata(joiner_path, "vocab_size", str(vocab_size))
