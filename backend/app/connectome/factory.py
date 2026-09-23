"""
Provider factory — selects the connectome provider based on configuration.

Configuration (via environment variables):

  CONNECTOME_PROVIDER   "synthetic" (default) or "real"
  NEUPRINT_TOKEN        neuPrint Bearer token  (required when provider=real)
  NEUPRINT_BASE_URL     neuPrint server URL    (default: https://neuprint.janelia.org)
  NEUPRINT_DATASET      Dataset identifier     (default: male-cns:v1.0)

Behaviour:
  - CONNECTOME_PROVIDER=synthetic  → SyntheticConnectomeProvider (no network, no token)
  - CONNECTOME_PROVIDER=real       → RealDrosophilaConnectomeProvider
      If NEUPRINT_TOKEN is missing, construction raises NeuPrintAuthenticationError
      immediately so the server can surface a clear error at startup.

Security:
  Credentials are read from environment variables only.
  NEVER hard-code tokens.  NEVER commit .env files.

Provider singleton:
  get_provider() returns a module-level singleton created once at import time.
  This avoids re-creating (and re-authenticating) the provider on each request.
"""
import logging
import os

from .provider import ConnectomeProvider
from .synthetic import SyntheticConnectomeProvider
from .real.client import NeuPrintClient
from .real.provider import RealDrosophilaConnectomeProvider
from .real.provenance import MALE_CNS_V1_PROVENANCE

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def _build_provider() -> ConnectomeProvider:
    """Read environment and construct the appropriate provider."""
    mode = os.environ.get("CONNECTOME_PROVIDER", "synthetic").strip().lower()

    if mode == "real":
        token = os.environ.get("NEUPRINT_TOKEN", "")
        base_url = os.environ.get(
            "NEUPRINT_BASE_URL", "https://neuprint.janelia.org"
        )
        dataset = os.environ.get("NEUPRINT_DATASET", "male-cns:v1.0")

        logger.info(
            "Connectome provider: REAL — dataset=%s base_url=%s",
            dataset,
            base_url,
        )

        # NeuPrintClient raises NeuPrintAuthenticationError if token is empty.
        client = NeuPrintClient(
            base_url=base_url,
            token=token,
            dataset=dataset,
        )
        return RealDrosophilaConnectomeProvider(
            client=client,
            provenance=MALE_CNS_V1_PROVENANCE,
        )

    # Default: synthetic
    if mode != "synthetic":
        logger.warning(
            "Unknown CONNECTOME_PROVIDER value %r; defaulting to synthetic.", mode
        )

    logger.info("Connectome provider: SYNTHETIC (development/test data)")
    return SyntheticConnectomeProvider(seed=42, num_neurons=100, edge_probability=0.05)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_provider_instance: ConnectomeProvider | None = None


def get_provider() -> ConnectomeProvider:
    """
    Return the application-wide connectome provider singleton.

    The singleton is created lazily on first call so that environment
    variables set after module import are respected.  Once created it
    is reused for the lifetime of the process.
    """
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = _build_provider()
    return _provider_instance


def reset_provider() -> None:
    """
    Reset the provider singleton.

    Used in tests to allow provider switching between test cases.
    Should not be called in production code.
    """
    global _provider_instance
    _provider_instance = None
