"""Compliance rule engine evaluation tool."""

import operator
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from aerodesign_ai.tools.base import BaseTool, ToolResult
from aerodesign_ai.models.schemas import ComplianceReport

CONFIG_DIR = Path(__file__).parent.parent / "config"


class RuleEvaluator:
    """Rule evaluation engine for compliance checking."""

    OPERATORS = {
        ">": operator.gt,
        "<": operator.lt,
        ">=": operator.ge,
        "<=": operator.le,
        "==": operator.eq,
        "!=": operator.ne,
    }

    def __init__(self, rules_config: Dict[str, Any]):
        self.rules = rules_config.get("rules", [])
        self.weight_limits = rules_config.get("weight_limits", {})
        self.performance_targets = rules_config.get("performance_targets", {})

    def _extract_field(self, geometry: Dict[str, Any], field_path: str) -> Any:
        """Extract a field from geometry using dot notation.

        Handles two cases:
        1. geometry.field -> returns geometry['field']
        2. field directly -> returns geometry['field']
        """
        parts = field_path.strip().split(".")
        value = geometry
        for part in parts:
            if part == "geometry":
                continue  # Skip the geometry prefix
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        return value

    def _evaluate_condition(self, condition: str, geometry: Dict[str, Any], **context) -> bool:
        """Evaluate a single condition string.

        Supports:
        - simple comparisons: "geometry.field >= value"
        - chained comparisons: "5 <= geometry.aspect_ratio <= 15"
        """
        condition = condition.strip()

        # Handle chained comparisons (e.g., "5 <= geometry.aspect_ratio <= 15")
        chain_match = re.match(r"(.+)\s*<=\s*(.+)\s*<=\s*(.+)", condition)
        if chain_match:
            left_val = float(chain_match.group(1))
            field_path = chain_match.group(2).strip()
            right_val = float(chain_match.group(3))
            field_val = self._extract_field(geometry, field_path)
            if field_val is None:
                return False
            return left_val <= field_val <= right_val

        # Handle simple comparisons
        for op_symbol, op_func in self.OPERATORS.items():
            if op_symbol in condition:
                parts = condition.split(op_symbol)
                if len(parts) == 2:
                    left = parts[0].strip()
                    route = parts[1].strip()
                    try:
                        left_val = float(left) if left.replace(".", "").replace("-", "").isdigit() else self._extract_field(geometry, left)
                        right_val = float(route) if route.replace(".", "").replace("-", "").isdigit() else self._extract_field(geometry, route)
                        if left_val is not None and right_val is not None:
                            return op_func(left_val, right_val)
                    except (ValueError, TypeError):
                        continue

        return False

    def evaluate(self, geometry: Dict[str, Any], **context) -> ComplianceReport:
        """Evaluate all rules against the geometry.

        Args:
            geometry: Aircraft geometry dictionary
            **context: Additional context (payload, material, etc.)

        Returns:
            ComplianceReport with evaluation results
        """
        violations = []
        warnings = []
        checked_rules = []

        for rule in self.rules:
            rule_id = rule["id"]
            condition = rule["condition"]
            severity = rule["severity"]
            message = rule["message"]

            checked_rules.append(rule_id)

            try:
                passed = self._evaluate_condition(condition, geometry, **context)
            except Exception as e:
                passed = False
                message = f"{message} (evaluation error: {str(e)})"

            if not passed:
                if severity == "critical":
                    violations.append(message)
                else:
                    warnings.append(message)

        return ComplianceReport(
            passed=len(violations) == 0,
            violations=violations,
            warnings=warnings,
            checked_rules=checked_rules,
            timestamp=datetime.utcnow(),
        )


class RunComplianceCheck(BaseTool[ComplianceReport]):
    """Run compliance check against rule engine."""

    name = "run_compliance_check"
    description = "Evaluate geometry against compliance rules. Returns a ComplianceReport with violations."

    _config: Optional[Dict[str, Any]] = None
    _evaluator: Optional[RuleEvaluator] = None

    def __init__(self, config_path: Optional[Path] = None):
        self._config_path = config_path or (CONFIG_DIR / "rules.yaml")
        self._load_config()

    def _load_config(self) -> None:
        """Load rules configuration."""
        if self._config_path.exists():
            with open(self._config_path, "r") as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = {"rules": [], "weight_limits": {}, "performance_targets": {}}
        self._evaluator = RuleEvaluator(self._config)

    def call(self, geometry: Dict[str, Any], payload: Optional[float] = None, **kwargs) -> ToolResult[ComplianceReport]:
        """Evaluate geometry against compliance rules.

        Args:
            geometry: Aircraft geometry dictionary
            payload: Payload in tonnes (optional)

        Returns:
            ToolResult containing ComplianceReport
        """
        try:
            report = self._evaluator.evaluate(geometry, payload=payload)
            metadata = {
                "total_rules": len(report.checked_rules),
                "critical_violations": len(report.violations),
                "warnings": len(report.warnings),
            }
            return ToolResult.ok(report, metadata)

        except Exception as e:
            return ToolResult.err(f"Error evaluating compliance: {str(e)}")

    def validate_inputs(self, geometry: Dict[str, Any], **kwargs) -> bool:
        """Validate geometry input."""
        return isinstance(geometry, dict)
