from pathlib import Path


def convert_stub(output_path: str) -> None:
    Path(output_path).write_bytes(b"TFLITE_PLACEHOLDER")
