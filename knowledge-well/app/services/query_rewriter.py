# app/services/query_rewriter.py
from __future__ import annotations
import json, re
from typing import Dict, List, Optional
from ..core.config import settings
from .openai_client import OpenAIClient

SYSTEM = (
    "You rewrite user questions for a packaging knowledge-graph search. "
    "Return compact domain terms; avoid filler."
)

INSTRUCTIONS = """Return ONLY valid JSON (no code fences) with:
{
  "domain_phrases": ["multi word phrases"],
  "keywords": ["single tokens"]
}
Rules:
- Lowercase; 1–4 items per list.
- Exclude filler: can, you, find, need, related, please, etc.
- Prefer packaging/3D integration terms (e.g., 'hybrid bonding', 'advanced packaging', 'die-to-wafer').
- If unsure, guess from technical hints.

Examples:
Q: "problems in hybrid bonding for advanced packaging?"
{"domain_phrases":["hybrid bonding","advanced packaging"],"keywords":["bonding","packaging"]}

Q: "D2W hybrid-bonding defects and mitigation?"
{"domain_phrases":["die-to-wafer","hybrid bonding"],"keywords":["d2w","defects","mitigation"]}

Question:
"""

class QueryRewriter:
    """OpenAI-backed rewriter that returns strict JSON with phrases/keywords."""
    def __init__(self, model: Optional[str] = None, timeout_seconds: Optional[int] = None):
        self.model = model or settings.REWRITER_MODEL
        self.timeout = int(timeout_seconds or settings.REWRITER_TIMEOUT_SECONDS)
        self.client = OpenAIClient(
            api_key=settings.OPENAI_API_KEY,
            model=self.model,
            timeout_seconds=self.timeout,
            use_responses_api=True,
        )

    def rewrite(self, question: str) -> Dict[str, List[str]]:
        text = self.client.generate(
            prompt=INSTRUCTIONS + question.strip(),
            system=SYSTEM,
            temperature=0.0,
            stream=False,
        )
        data = self._safe_json(text) or self._safe_json(self._extract_json_block(text)) or {}
        phrases = self._norm_list(data.get("domain_phrases", []))
        keywords = self._norm_list(data.get("keywords", []))
        return {"domain_phrases": phrases, "keywords": keywords}

    @staticmethod
    def _safe_json(s: str | None):
        if not s: return None
        try: return json.loads(s)
        except Exception: return None

    @staticmethod
    def _extract_json_block(text: str) -> str | None:
        m = re.search(r"\{[\s\S]*\}", text)
        return m.group(0) if m else None

    @staticmethod
    def _norm_list(xs) -> List[str]:
        out, seen = [], set()
        if not isinstance(xs, list): return out
        for x in xs:
            if not isinstance(x, str): continue
            v = re.sub(r"\s+", " ", x.strip().lower())
            if v and v not in seen:
                out.append(v); seen.add(v)
        return out
