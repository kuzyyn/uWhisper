import onnx
import os

model_path = os.path.expanduser("~/.cache/uwhisper/parakeet_model/encoder.int8.onnx")

try:
    model = onnx.load(model_path)
    print(f"Inputs for {model_path}:")
    for input_node in model.graph.input:
        print(f"  Name: {input_node.name}")
        shape = []
        for d in input_node.type.tensor_type.shape.dim:
            if d.dim_value:
                shape.append(d.dim_value)
            elif d.dim_param:
                shape.append(d.dim_param)
            else:
                shape.append("?")
        print(f"  Shape: {shape}")
        
except Exception as e:
    print(f"Error: {e}")
