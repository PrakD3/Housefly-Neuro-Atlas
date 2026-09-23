"""
HTTP client for the neuPrint REST API.

Official API: https://neuprint.janelia.org
Swagger spec: https://neuprint.janelia.org/api/help/swagger.yaml

Authentication:
  All endpoints require a Bearer token (JWT).
  Obtain your token from https://neuprint.janelia.org → Account page after
  signing in with Google.
  Set the token in the environment variable NEUPRINT_TOKEN.
  NEVER hard-code or commit tokens.

Rate limiting:
  neuPrint does not publish explicit rate limits.  This client enforces a
  conservative per-request timeout and raises NeuPrintRateLimitError on
  HTTP 429 responses.
"""
import httpx
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class NeuPrintError(Exception):
    """Base class for all neuPrint client errors."""


class NeuPrintAuthenticationError(NeuPrintError):
    """Raised when the API token is missing or rejected (HTTP 401/403)."""


class NeuPrintConnectionError(NeuPrintError):
    """Raised on network-level failures or timeouts."""


class NeuPrintRateLimitError(NeuPrintError):
    """Raised when the server responds with HTTP 429."""


class NeuPrintDatasetError(NeuPrintError):
    """Raised when the requested dataset is not available (HTTP 404)."""


class NeuPrintResponseError(NeuPrintError):
    """Raised when the server returns an unexpected or malformed response."""


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class NeuPrintClient:
    """
    Thin HTTP wrapper around the neuPrint REST API.

    Responsibilities:
      - Authentication via Bearer token
      - POST /api/custom/custom  (Cypher query execution)
      - GET  /api/dbmeta/datasets  (dataset listing)
      - Error classification into domain-specific exceptions

    This class does NOT perform any biological normalization.
    The provider layer (provider.py) is responsible for mapping raw
    neuPrint responses to internal models.
    """

    def __init__(
        self,
        base_url: str,
        token: str,
        dataset: str,
        timeout: float = 30.0,
    ) -> None:
        if not token:
            raise NeuPrintAuthenticationError(
                "NEUPRINT_TOKEN is not set. "
                "Obtain a token from https://neuprint.janelia.org (Account page)."
            )
        self._base_url = base_url.rstrip("/")
        self._dataset = dataset
        self._timeout = timeout
        self._headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def query_cypher(self, cypher: str) -> Dict[str, Any]:
        """
        Execute a read-only Cypher query against the configured dataset.

        Returns the raw neuPrint response dict with 'columns' and 'data'.

        Raises:
            NeuPrintAuthenticationError  — HTTP 401/403
            NeuPrintRateLimitError       — HTTP 429
            NeuPrintDatasetError         — HTTP 404
            NeuPrintResponseError        — HTTP 5xx or malformed body
            NeuPrintConnectionError      — network failure / timeout
        """
        url = f"{self._base_url}/api/custom/custom"
        payload = {"cypher": cypher, "dataset": self._dataset}

        logger.debug("neuPrint Cypher query: %s", cypher[:200])

        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.post(url, json=payload, headers=self._headers)
        except httpx.TimeoutException as exc:
            raise NeuPrintConnectionError(
                f"Request to neuPrint timed out after {self._timeout}s: {exc}"
            ) from exc
        except httpx.RequestError as exc:
            raise NeuPrintConnectionError(
                f"Network error communicating with neuPrint: {exc}"
            ) from exc

        self._raise_for_status(response)

        try:
            return response.json()
        except Exception as exc:
            raise NeuPrintResponseError(
                f"neuPrint returned a non-JSON body: {exc}"
            ) from exc

    def get_datasets(self) -> Dict[str, Any]:
        """
        Retrieve dataset metadata from GET /api/dbmeta/datasets.

        Raises same exceptions as query_cypher.
        """
        url = f"{self._base_url}/api/dbmeta/datasets"
        try:
            with httpx.Client(timeout=self._timeout) as client:
                response = client.get(url, headers=self._headers)
        except httpx.TimeoutException as exc:
            raise NeuPrintConnectionError(
                f"Timeout fetching dataset list: {exc}"
            ) from exc
        except httpx.RequestError as exc:
            raise NeuPrintConnectionError(
                f"Network error fetching dataset list: {exc}"
            ) from exc

        self._raise_for_status(response)

        try:
            return response.json()
        except Exception as exc:
            raise NeuPrintResponseError(
                f"neuPrint datasets endpoint returned non-JSON: {exc}"
            ) from exc

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _raise_for_status(self, response: httpx.Response) -> None:
        """Map HTTP status codes to domain exceptions."""
        code = response.status_code
        if code == 200:
            return
        if code in (401, 403):
            raise NeuPrintAuthenticationError(
                f"neuPrint authentication failed (HTTP {code}). "
                "Check your NEUPRINT_TOKEN."
            )
        if code == 404:
            raise NeuPrintDatasetError(
                f"neuPrint dataset not found (HTTP {code}). "
                f"Dataset: {self._dataset}"
            )
        if code == 429:
            raise NeuPrintRateLimitError(
                "neuPrint rate limit exceeded (HTTP 429). Please retry later."
            )
        if code >= 500:
            raise NeuPrintResponseError(
                f"neuPrint server error (HTTP {code}): {response.text[:200]}"
            )
        raise NeuPrintResponseError(
            f"Unexpected HTTP {code} from neuPrint: {response.text[:200]}"
        )
