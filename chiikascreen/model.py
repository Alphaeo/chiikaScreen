"""Local vision-language model wrapper (Qwen2-VL / Qwen2.5-VL, GGUF, CPU inference).

This machine has 8 GB of RAM and no discrete GPU, which leaves very little
headroom for the vision tower's compute buffers. The bigger Qwen2.5-VL-3B
(F16 mmproj) crashes intermittently with a native access-violation under
memory pressure, so we prefer the much lighter Qwen2-VL-2B (Q8 mmproj) when
it's available, and fall back to the 3B if that's the only one downloaded.
"""

import base64
import io
import os
import threading
from pathlib import Path

from PIL import Image

MODEL_DIR = Path(__file__).resolve().parent.parent / "models"

CANDIDATES = [
    # Q8_0 mmproj (~845MB) instead of F16 (~1.34GB) - smaller vision-tower
    # compute buffers, which is what was tipping this machine into native
    # access-violation crashes during image encoding.
    (MODEL_DIR / "Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf", MODEL_DIR / "mmproj-Qwen2.5-VL-3B-Instruct-Q8_0.gguf"),
]

# Fallback resolution used if a query crashes at the normal size - a smaller
# image means a smaller compute buffer, which is what tips native OOM crashes.
FALLBACK_MAX_DIMENSION = 512


class ScreenModel:
    """Wraps llama.cpp's Qwen2-VL/2.5-VL chat handler behind a simple ask(image, question) API."""

    def __init__(self):
        text_model, mmproj = next(
            ((t, m) for t, m in CANDIDATES if t.exists() and m.exists()), (None, None)
        )
        if text_model is None:
            expected = ", ".join(f"{t.name} + {m.name}" for t, m in CANDIDATES)
            raise FileNotFoundError(f"Aucun modele trouve dans {MODEL_DIR}. Attendu l'un de: {expected}")

        from llama_cpp import Llama
        from llama_cpp.llama_chat_format import Qwen25VLChatHandler

        self._lock = threading.Lock()
        chat_handler = Qwen25VLChatHandler(clip_model_path=str(mmproj), verbose=False)
        self.llm = Llama(
            model_path=str(text_model),
            chat_handler=chat_handler,
            n_ctx=2048,
            n_threads=os.cpu_count(),
            logits_all=False,
            use_mmap=False,
            verbose=False,
        )

    def ask(self, image: Image.Image, question: str) -> str:
        with self._lock:
            try:
                return self._ask_once(image, question)
            except OSError:
                # Native crash in the vision encoder (out-of-memory territory
                # on this machine). Retry once with a much smaller image
                # instead of surfacing a raw access-violation to the user.
                small = image.copy()
                small.thumbnail((FALLBACK_MAX_DIMENSION, FALLBACK_MAX_DIMENSION), Image.LANCZOS)
                return self._ask_once(small, question)

    def _ask_once(self, image: Image.Image, question: str) -> str:
        data_uri = _to_data_uri(image)
        resp = self.llm.create_chat_completion(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_uri}},
                        {"type": "text", "text": question},
                    ],
                }
            ],
            max_tokens=512,
        )
        return resp["choices"][0]["message"]["content"].strip()


def _to_data_uri(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"
