"""Persistent, revision-pinned model cache; no audio files are created."""
import os
from pathlib import Path

MODEL = "theaifactorybv/murmel-flash-m-v5"


def load_backend(options, data_dir):
    from huggingface_hub import snapshot_download
    import torch
    from murmel_flash import Transcriber

    threads = options.get("cpu_threads", 0) or max(1, min(4, (os.cpu_count() or 2) - 1))
    torch.set_num_threads(threads)
    root = Path(data_dir)
    cache = root / "models"
    revision = options.get("model_revision", "main")
    marker = root / "model-path.json"
    import json
    if marker.exists():
        saved = json.loads(marker.read_text())
        if saved["revision"] == revision and Path(saved["path"]).is_dir():
            transcriber = Transcriber.from_pretrained(saved["path"], device="cpu")
            return lambda audio: transcriber.transcribe(audio, beam=options.get("beam_size", 4), hotwords=options.get("hotwords", []))["text"]
    # Exact commit revisions keep releases reproducible. Cached files permit
    # startup without a network connection or a still-valid download token.
    try:
        model_dir = snapshot_download(MODEL, revision=revision, cache_dir=cache,
                                      local_files_only=True)
    except Exception:
        model_dir = snapshot_download(MODEL, revision=revision, cache_dir=cache,
                                      token=options.get("hf_token") or os.environ.get("HF_TOKEN"),
                                      allow_patterns=["*.yaml", "*.json", "*.model", "*.safetensors"])
    transcriber = Transcriber.from_pretrained(model_dir, device="cpu")
    marker.write_text(json.dumps({"revision": revision, "path": model_dir}))

    def transcribe(audio):
        return transcriber.transcribe(audio, beam=options.get("beam_size", 4),
                                      hotwords=options.get("hotwords", []))["text"]
    return transcribe
