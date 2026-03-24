"""UDC PolicyGuard — YAML-based policy definition store."""

from pathlib import Path
from typing import Any

import yaml
import structlog

logger = structlog.get_logger(__name__)


class PolicyStore:
    """Load, merge, and serve policy definitions from YAML files.

    Loads YAML policy definitions from a directory, merging base
    defaults with type-specific overrides.
    """

    def __init__(self) -> None:
        self._policies: list[dict[str, Any]] = []
        self._yaml_dir: Path | None = None

    def load_policies(self, yaml_dir: str | Path) -> None:
        """Load all policy YAML files from the given directory.

        Args:
            yaml_dir: Path to directory containing YAML policy files.
        """
        self._yaml_dir = Path(yaml_dir)
        self._policies = []

        if not self._yaml_dir.is_dir():
            logger.warning("policy_store.dir_not_found", path=str(self._yaml_dir))
            return

        for yaml_file in sorted(self._yaml_dir.glob("*.yaml")):
            try:
                raw = yaml_file.read_text(encoding="utf-8")
                data = yaml.safe_load(raw)
                if data and "policies" in data:
                    for policy in data["policies"]:
                        policy.setdefault("source_file", yaml_file.name)
                        policy.setdefault("enabled", True)
                        self._policies.append(policy)
                        logger.debug(
                            "policy_store.loaded_policy",
                            name=policy.get("name"),
                            rule_type=policy.get("rule_type"),
                            source=yaml_file.name,
                        )
            except yaml.YAMLError as exc:
                logger.error("policy_store.parse_error", file=yaml_file.name, error=str(exc))
            except OSError as exc:
                logger.error("policy_store.read_error", file=yaml_file.name, error=str(exc))

        logger.info("policy_store.loaded", total=len(self._policies))

    def get_all(self) -> list[dict]:
        """Return all loaded policy definitions."""
        return [p for p in self._policies if p.get("enabled", True)]

    def get_by_type(self, rule_type: str) -> list[dict]:
        """Return policies matching the given rule type.

        Args:
            rule_type: The policy rule type to filter on.
        """
        return [
            p for p in self._policies
            if p.get("enabled", True) and p.get("rule_type") == rule_type
        ]

    def reload(self) -> None:
        """Reload all policies from disk."""
        if self._yaml_dir is None:
            logger.warning("policy_store.reload_no_dir")
            return
        logger.info("policy_store.reloading", path=str(self._yaml_dir))
        self.load_policies(self._yaml_dir)
