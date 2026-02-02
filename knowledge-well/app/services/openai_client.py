from __future__ import annotations
from typing import Optional, Dict, Any, Tuple
from openai import OpenAI

class OpenAIClient:
    """
    Thin wrapper so it matches your other clients.
    Now supports return_meta=True to provide usage + finish_reason.
    """
    def __init__(
        self,
        api_key: Optional[str],
        model: Optional[str],
        base_url: Optional[str] = None,   # keep None for api.openai.com
        timeout_seconds: int = 600,       # generous; compare apples-to-apples
        use_responses_api: bool = True,   # set False to use Chat Completions instead
    ):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.use_responses_api = use_responses_api

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.2,
        options: Optional[Dict[str, Any]] = None,
        stream: bool = False,              # keep False to mirror your current behavior
        return_meta: bool = False,         # <-- NEW
    ):
        if stream:
            raise NotImplementedError("stream=True not supported in OpenAIClient.generate")

        if self.use_responses_api:
            # Responses API: combine system + user for a simple single-input call
            text_input = prompt if not system else f"[SYSTEM]\n{system}\n\n[USER]\n{prompt}"
            kwargs: Dict[str, Any] = dict(
                model=self.model,
                input=text_input,
                temperature=temperature,
                timeout=self.timeout_seconds,
            )
            if options:
                kwargs.update(options)

            r = self.client.responses.create(**kwargs)

            # Text extraction
            text = getattr(r, "output_text", "") or (
                r.output[0].content[0].text if getattr(r, "output", None) else ""
            )

            if not return_meta:
                return text

            # Usage + finish_reason (defensive across SDK variants)
            usage = getattr(r, "usage", None) or getattr(r, "usage_metadata", None)
            input_tokens  = getattr(usage, "input_tokens",  None) or getattr(usage, "prompt_tokens", None)
            output_tokens = getattr(usage, "output_tokens", None) or getattr(usage, "completion_tokens", None)
            total_tokens  = getattr(usage, "total_tokens",  None)

            finish_reason = None
            try:
                if getattr(r, "output", None):
                    finish_reason = getattr(r.output[0], "finish_reason", None)
            except Exception:
                finish_reason = None

            meta = {
                "provider": "OPENAI",
                "model": self.model,
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": total_tokens,
                "finish_reason": finish_reason,
            }
            return text, meta

        else:
            # Chat Completions
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            kwargs: Dict[str, Any] = dict(
                model=self.model,
                messages=messages,
                temperature=temperature,
                timeout=self.timeout_seconds,
            )
            if options:
                kwargs.update(options)

            r = self.client.chat.completions.create(**kwargs)

            text = r.choices[0].message.content if r.choices else ""

            if not return_meta:
                return text

            usage = getattr(r, "usage", None)
            input_tokens  = getattr(usage, "prompt_tokens", None) if usage else None
            output_tokens = getattr(usage, "completion_tokens", None) if usage else None
            total_tokens  = getattr(usage, "total_tokens", None) if usage else None
            finish_reason = r.choices[0].finish_reason if r.choices else None

            meta = {
                "provider": "OPENAI",
                "model": self.model,
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens,
                "total_tokens": total_tokens,
                "finish_reason": finish_reason,
            }
            return text, meta
