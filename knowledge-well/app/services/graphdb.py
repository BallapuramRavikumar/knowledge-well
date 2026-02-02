from __future__ import annotations
import time
from typing import Optional, Dict, Any
import httpx
from .utils import to_query_params_compat

class GraphDBClient:
    """
    Minimal GraphDB SPARQL client with BASIC or GDB token auth.
    - GDB login: POST {base}/rest/login/{username} with header X-GraphDB-Password
                 reads token from response 'Authorization' header.
    """
    def __init__(
        self,
        base_url: str,
        repository: str,
        auth_mode: str = "BASIC",
        username: str = "",
        password: str = "",
        verify_tls: bool = True,
        timeout: int = 30,
        token_ttl_seconds: int = 36000,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.repository = repository
        self.auth_mode = (auth_mode or "BASIC").upper()
        self.username = username or ""
        self.password = password or ""
        self.verify_tls = verify_tls
        self.timeout = timeout
        self.token_ttl_seconds = token_ttl_seconds

        self._client = httpx.Client(timeout=self.timeout, verify=self.verify_tls)
        self._token: Optional[str] = None
        self._token_expiry: float = 0.0

    # ---------- Auth helpers ----------

    def _auth_basic(self):
        if self.username and self.password:
            return (self.username, self.password)
        return None

    def _gdb_token(self) -> str:
        """Login and cache token using GraphDB's /rest/login/{user} flow."""
        now = time.time()
        if self._token and now < (self._token_expiry - 60):
            return self._token
        if not (self.username and self.password):
            raise RuntimeError("GRAPHDB_USERNAME/PASSWORD not set for GDB auth")

        url = f"{self.base_url}/rest/login/{self.username}"
        # Important: no redirects; token is in the response headers
        r = self._client.post(
            url,
            headers={"X-GraphDB-Password": self.password},
            follow_redirects=False,
        )
        r.raise_for_status()
        token = r.headers.get("Authorization")
        if not token:
            raise RuntimeError("GraphDB login succeeded but no Authorization header returned")
        self._token = token
        self._token_expiry = now + self.token_ttl_seconds
        return token

    def login_if_needed(self) -> None:
        if self.auth_mode == "GDB":
            self._gdb_token()  # ensures self._token is set/refreshed

    def _headers(self, accept: str = "application/sparql-results+json") -> Dict[str, str]:
        h = {"Accept": accept}
        if self.auth_mode == "GDB":
            # ensure token present
            self._gdb_token()
            h["Authorization"] = self._token  # e.g., "GDB eyJ..."
        return h

    # ---------- SPARQL APIs ----------

    def sparql_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """POST SPARQL SELECT/ASK to /repositories/{repo}, expect JSON."""
        q = to_query_params_compat(query, params) if params else query
        url = f"{self.base_url}/repositories/{self.repository}"
        headers = self._headers(accept="application/sparql-results+json")
        auth = self._auth_basic() if self.auth_mode == "BASIC" else None

        resp = self._client.post(url, headers=headers, auth=auth, data={"query": q})
        resp.raise_for_status()
        return resp.json()

    def sparql_query_raw(self, query: str, accept: str) -> httpx.Response:
        """Same as sparql_query but caller controls Accept, returns raw response."""
        url = f"{self.base_url}/repositories/{self.repository}"
        headers = self._headers(accept=accept)
        auth = self._auth_basic() if self.auth_mode == "BASIC" else None
        return self._client.post(url, headers=headers, auth=auth, data={"query": query})

    def sparql_update(self, update: str) -> None:
        """POST SPARQL UPDATE to /repositories/{repo}/statements."""
        url = f"{self.base_url}/repositories/{self.repository}/statements"
        headers = {"Content-Type": "application/sparql-update"}
        # merge auth header if needed
        headers.update(self._headers(accept="*/*"))
        auth = self._auth_basic() if self.auth_mode == "BASIC" else None

        resp = self._client.post(url, headers=headers, auth=auth, content=update.encode("utf-8"))
        resp.raise_for_status()
