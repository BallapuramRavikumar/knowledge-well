
from __future__ import annotations
# import re

def to_query_params_compat(query: str, params: dict) -> str:
    """
    Very naive string templating for SPARQL. Prefer server-side bindings when available.
    Escapes double quotes inside values.
    """
    q = query
    for k, v in params.items():
        if isinstance(v, str):
            safe = v.replace('"', '\\"')
            q = q.replace(f"{{{{{k}}}}}", f'"{safe}"')
        else:
            q = q.replace(f"{{{{{k}}}}}", str(v))
    return q
