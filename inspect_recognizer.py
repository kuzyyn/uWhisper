import sherpa_onnx
import inspect

print("OfflineRecognizer constructor:")
try:
    print(sherpa_onnx.OfflineRecognizer.__init__.__doc__)
except:
    print("No docstring for __init__")

print("\nOfflineRecognizer.from_transducer:")
try:
    print(sherpa_onnx.OfflineRecognizer.from_transducer.__doc__)
except:
    print("No docstring for from_transducer")
