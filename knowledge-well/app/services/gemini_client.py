# app/services/gemini_client.py
from __future__ import annotations
from typing import Optional, Dict, Any, Tuple
import google.generativeai as genai


class GeminiClient:
    """
    Minimal wrapper around Google Gemini via the `google-generativeai` SDK.
    Mirrors .generate(...) shape of your other clients and can return meta.
    """

    def __init__(self,
                 api_key: Optional[str],
                 model: Optional[str],
                 timeout_seconds: int = 600):
        self.model_name = model
        self.timeout_seconds = timeout_seconds
        genai.configure(api_key=api_key)

    def generate(self,
                 prompt: str,
                 system: Optional[str] = None,
                 temperature: float = 0.2,
                 options: Optional[Dict[str, Any]] = None,
                 stream: bool = False,
                 return_meta: bool = False):
        if stream:
            # Keep parity with other wrappers (we're not streaming in this app)
            raise NotImplementedError("stream=True not supported in GeminiClient.generate")

        generation_config: Dict[str, Any] = {"temperature": float(temperature)}
        if options:
            generation_config.update(options)

        # You can pass a system instruction per call
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system if system else None,
        )

        resp = model.generate_content(
            prompt,
            generation_config=generation_config,
            request_options={"timeout": self.timeout_seconds},
        )
        text = getattr(resp, "text", "") or ""

        if not return_meta:
            return text

        # Usage metrics (SDK versions differ slightly; handle both)
        usage = getattr(resp, "usage_metadata", None)
        input_tokens = getattr(usage, "input_tokens", None) or getattr(usage, "prompt_token_count", None)
        output_tokens = getattr(usage, "output_tokens", None) or getattr(usage, "candidates_token_count", None)
        total_tokens = getattr(usage, "total_tokens", None) or getattr(usage, "total_token_count", None)

        finish_reason = None
        try:
            finish_reason = resp.candidates[0].finish_reason
        except Exception:
            pass

        meta = {
            "provider": "GEMINI",
            "model": self.model_name,
            "prompt_tokens": input_tokens,
            "completion_tokens": output_tokens,
            "total_tokens": total_tokens,
            "finish_reason": finish_reason,
        }
        return text, meta
