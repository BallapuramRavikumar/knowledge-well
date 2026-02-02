
from __future__ import annotations
import httpx
from typing import List

class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3.1:8b", timeout: int = 600):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.client = httpx.Client(timeout=timeout)

    def generate(self, prompt: str, system: str = "", temperature: float = 0.2) -> str:
        # Non-streaming generate
        payload = {
            "model": self.model,
            "prompt": prompt if not system else f"<<SYS>>\n{system}\n<</SYS>>\n{prompt}",
            "stream": False,
            "options": {"temperature": temperature},
        }
        r = self.client.post(f"{self.base_url}/api/generate", json=payload)
        r.raise_for_status()
        data = r.json()
        return data.get("response", "")
