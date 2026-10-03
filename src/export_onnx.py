"""
Exports trained PyTorch Myanmar Name Model to ONNX and INT8 quantized formats.
Enables high-performance CPU/GPU inference (<2ms) without PyTorch dependency,
making it deployable in PHP (via FFI/ONNX Runtime) or lightweight microservices.
"""

import os
import argparse
import torch
from transformers import AutoTokenizer, AutoModel
import onnx
from onnxruntime.quantization import quantize_dynamic, QuantType


def export_to_onnx(model_path: str, output_onnx_path: str, quantize: bool = True):
    print(f"Loading PyTorch model from {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModel.from_pretrained(model_path)
    model.eval()

    # Dummy input
    dummy_text = "Kyaw Swar"
    inputs = tokenizer(dummy_text, padding="max_length", max_length=32, return_tensors="pt")

    os.makedirs(os.path.dirname(output_onnx_path), exist_ok=True)

    print(f"Exporting to ONNX -> {output_onnx_path}...")
    torch.onnx.export(
        model,
        (inputs["input_ids"], inputs["attention_mask"]),
        output_onnx_path,
        input_names=["input_ids", "attention_mask"],
        output_names=["last_hidden_state"],
        dynamic_axes={
            "input_ids": {0: "batch_size", 1: "sequence_length"},
            "attention_mask": {0: "batch_size", 1: "sequence_length"},
            "last_hidden_state": {0: "batch_size", 1: "sequence_length"},
        },
        opset_version=14,
    )

    print("Checking ONNX model validity...")
    onnx_model = onnx.load(output_onnx_path)
    onnx.checker.check_model(onnx_model)
    orig_size_mb = os.path.getsize(output_onnx_path) / (1024 * 1024)
    print(f"Base ONNX model exported successfully! Size: {orig_size_mb:.2f} MB")

    if quantize:
        quantized_path = output_onnx_path.replace(".onnx", "-int8.onnx")
        print(f"Quantizing to INT8 -> {quantized_path}...")
        quantize_dynamic(
            output_onnx_path,
            quantized_path,
            weight_type=QuantType.QInt8,
        )
        q_size_mb = os.path.getsize(quantized_path) / (1024 * 1024)
        print(f"INT8 Quantized ONNX model created! Size: {q_size_mb:.2f} MB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export PyTorch model to ONNX")
    parser.add_argument("--model_path", type=str, default="models/myanmar-name-encoder")
    parser.add_argument("--output_path", type=str, default="models/myanmar-name-encoder.onnx")
    parser.add_argument("--quantize", action="store_true", default=True)

    args = parser.parse_args()
    export_to_onnx(args.model_path, args.output_path, args.quantize)
