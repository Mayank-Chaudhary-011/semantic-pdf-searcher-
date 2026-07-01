# ============================================================
# embedder.py — unchanged from what you shared, aside from
# trimming the manual __main__ test block.
# ============================================================

import torch
from sentence_transformers import SentenceTransformer


def get_device():
    if torch.cuda.is_available():
        device = "cuda"
        print(f"[embedder] GPU detected: {torch.cuda.get_device_name(0)} — using GPU")
    else:
        device = "cpu"
        print("[embedder] No GPU detected — using CPU")
    return device


class Embedder:
    def __init__(self, model_name="paraphrase-multilingual-MiniLM-L12-v2"):
        self.device = get_device()
        print(f"[embedder] Loading model: {model_name} ...")
        self.model = SentenceTransformer(model_name, device=self.device)
        print("[embedder] Model loaded.")

    def embed_text(self, text):
        embedding = self.model.encode([text])[0]
        return embedding.tolist()

    def embed_batch(self, texts):
        embeddings = self.model.encode(texts, show_progress_bar=False)
        return [e.tolist() for e in embeddings]
