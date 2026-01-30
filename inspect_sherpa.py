import sherpa_onnx

print("Inspecting OfflineTransducerModelConfig:")
try:
    print(sherpa_onnx.OfflineTransducerModelConfig().__dict__)
    # Or checking help
    help(sherpa_onnx.OfflineTransducerModelConfig)
except Exception as e:
    print(e)
