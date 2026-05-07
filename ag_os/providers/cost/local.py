"""Local JSON cost provider (DEFAULT)."""

import json
from pathlib import Path

from ag_os.providers.cost import CostProvider
from ag_os.providers.registry import register

_AG_HOME = Path.home() / ".antigravity"
_PRICING_FILE = _AG_HOME / "pricing.json"
_SPEND_FILE = _AG_HOME / "spend.json"

_DEFAULT_PRICING = {
    "tiers": {
        "standard_cpu": 1.00,
        "gpu_small": 2.50,
        "gpu_large": 8.00,
    }
}

_DEFAULT_SPEND = {
    "current_spend": 0.00,
    "last_updated": "",
}


@register("cost", "local")
class LocalCostProvider(CostProvider):
    """Reads pricing and spend from local JSON files.

    Files are stored at ~/.antigravity/pricing.json and ~/.antigravity/spend.json.
    If the files do not exist, they are created with sensible defaults.
    """

    def __init__(self, **kwargs):
        _AG_HOME.mkdir(parents=True, exist_ok=True)
        self._pricing = self._load_or_create(_PRICING_FILE, _DEFAULT_PRICING)
        self._spend = self._load_or_create(_SPEND_FILE, _DEFAULT_SPEND)

    @staticmethod
    def _load_or_create(path: Path, defaults: dict) -> dict:
        if path.is_file():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(defaults, f, indent=2)
        return dict(defaults)

    def get_current_spend(self) -> float:
        # Re-read on each call to pick up manual edits
        if _SPEND_FILE.is_file():
            with open(_SPEND_FILE, "r", encoding="utf-8") as f:
                self._spend = json.load(f)
        return float(self._spend.get("current_spend", 0.0))

    def get_tier_rate(self, tier: str) -> float:
        tiers = self._pricing.get("tiers", {})
        if tier not in tiers:
            available = sorted(tiers.keys())
            raise ValueError(
                f"Unknown pricing tier '{tier}'. Available: {available}. "
                f"Edit {_PRICING_FILE} to add custom tiers."
            )
        return float(tiers[tier])
