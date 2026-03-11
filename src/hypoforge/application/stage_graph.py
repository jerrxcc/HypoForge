"""Stage Navigator for cross-stage navigation and data management.

This module provides the StageNavigator that manages stage dependencies,
backtracking rules, and data preservation strategies.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

from hypoforge.domain.schemas import StageName

if TYPE_CHECKING:
    from hypoforge.infrastructure.db.repository import RunRepository


logger = logging.getLogger(__name__)


class DataStatus(Enum):
    """Status of data after backtracking."""
    VALID = "valid"
    PENDING_VALIDATION = "pending_validation"
    STALE = "stale"


@dataclass
class BacktrackRule:
    """Rule for backtracking from one stage to another."""
    from_stage: StageName
    to_stage: StageName
    reason_pattern: str
    data_to_preserve: list[str]
    data_to_regenerate: list[str]


# Define valid backtracking rules
BACKTRACK_RULES: list[BacktrackRule] = [
    BacktrackRule(
        from_stage="critic",
        to_stage="retrieval",
        reason_pattern="paper_coverage",
        data_to_preserve=["topic", "constraints"],
        data_to_regenerate=["selected_papers", "evidence_cards", "conflict_clusters"],
    ),
    BacktrackRule(
        from_stage="critic",
        to_stage="review",
        reason_pattern="evidence_quality",
        data_to_preserve=["selected_papers", "topic"],
        data_to_regenerate=["evidence_cards", "conflict_clusters"],
    ),
    BacktrackRule(
        from_stage="planner",
        to_stage="retrieval",
        reason_pattern="evidence_base",
        data_to_preserve=["topic", "constraints"],
        data_to_regenerate=["selected_papers", "evidence_cards", "conflict_clusters", "hypotheses"],
    ),
    BacktrackRule(
        from_stage="planner",
        to_stage="review",
        reason_pattern="evidence_support",
        data_to_preserve=["selected_papers", "topic"],
        data_to_regenerate=["evidence_cards", "conflict_clusters", "hypotheses"],
    ),
    BacktrackRule(
        from_stage="planner",
        to_stage="critic",
        reason_pattern="conflict_analysis",
        data_to_preserve=["selected_papers", "evidence_cards", "topic"],
        data_to_regenerate=["conflict_clusters", "hypotheses"],
    ),
]


class StageNavigator:
    """Navigator for cross-stage movement and data management.

    The StageNavigator handles:
    - Validating backtracking requests
    - Determining data preservation during backtracks
    - Managing stage dependencies
    - Tracking data status after modifications
    """

    # Stage execution order
    STAGE_ORDER: list[StageName] = ["retrieval", "review", "critic", "planner"]

    def __init__(self, repository: RunRepository) -> None:
        self._repository = repository
        self._data_status: dict[str, dict[str, DataStatus]] = {}
        self._logger = logging.getLogger(__name__)

    def can_backtrack_to(
        self,
        from_stage: StageName,
        to_stage: StageName,
    ) -> bool:
        """Check if backtracking from one stage to another is valid.

        Args:
            from_stage: The current stage
            to_stage: The target stage to backtrack to

        Returns:
            True if backtracking is allowed
        """
        # Can only backtrack to earlier stages
        from_idx = self.STAGE_ORDER.index(from_stage)
        to_idx = self.STAGE_ORDER.index(to_stage)

        if to_idx >= from_idx:
            self._logger.warning(
                "Invalid backtrack: can only backtrack to earlier stages",
                extra={"from": from_stage, "to": to_stage},
            )
            return False

        # Check if there's a valid backtrack rule
        for rule in BACKTRACK_RULES:
            if rule.from_stage == from_stage and rule.to_stage == to_stage:
                return True

        # Allow any backward movement for flexibility
        return True

    def get_data_to_preserve(
        self,
        from_stage: StageName,
        to_stage: StageName,
    ) -> list[str]:
        """Get list of data that should be preserved during backtrack.

        Args:
            from_stage: The current stage
            to_stage: The target stage

        Returns:
            List of data keys to preserve
        """
        for rule in BACKTRACK_RULES:
            if rule.from_stage == from_stage and rule.to_stage == to_stage:
                return rule.data_to_preserve

        # Default: preserve topic and constraints
        return ["topic", "constraints"]

    def get_data_to_regenerate(
        self,
        from_stage: StageName,
        to_stage: StageName,
    ) -> list[str]:
        """Get list of data that needs to be regenerated after backtrack.

        Args:
            from_stage: The current stage
            to_stage: The target stage

        Returns:
            List of data keys that need regeneration
        """
        for rule in BACKTRACK_RULES:
            if rule.from_stage == from_stage and rule.to_stage == to_stage:
                return rule.data_to_regenerate

        # Default: regenerate everything after target stage
        from_idx = self.STAGE_ORDER.index(from_stage)
        to_idx = self.STAGE_ORDER.index(to_stage)

        data_mapping = {
            "retrieval": ["selected_papers"],
            "review": ["evidence_cards"],
            "critic": ["conflict_clusters"],
            "planner": ["hypotheses"],
        }

        regenerate: list[str] = []
        for i in range(to_idx, from_idx + 1):
            stage = self.STAGE_ORDER[i]
            regenerate.extend(data_mapping.get(stage, []))

        return regenerate

    def get_next_stage(self, current_stage: StageName) -> StageName | None:
        """Get the next stage in the pipeline.

        Args:
            current_stage: The current stage

        Returns:
            The next stage name, or None if at the end
        """
        try:
            current_idx = self.STAGE_ORDER.index(current_stage)
            if current_idx < len(self.STAGE_ORDER) - 1:
                return self.STAGE_ORDER[current_idx + 1]
        except ValueError:
            pass
        return None

    def get_previous_stage(self, current_stage: StageName) -> StageName | None:
        """Get the previous stage in the pipeline.

        Args:
            current_stage: The current stage

        Returns:
            The previous stage name, or None if at the beginning
        """
        try:
            current_idx = self.STAGE_ORDER.index(current_stage)
            if current_idx > 0:
                return self.STAGE_ORDER[current_idx - 1]
        except ValueError:
            pass
        return None

    def mark_data_status(
        self,
        run_id: str,
        data_type: str,
        status: DataStatus,
    ) -> None:
        """Mark the status of specific data.

        Args:
            run_id: The run identifier
            data_type: Type of data (e.g., 'evidence_cards')
            status: New status for the data
        """
        if run_id not in self._data_status:
            self._data_status[run_id] = {}
        self._data_status[run_id][data_type] = status

        self._logger.debug(
            "Data status updated",
            extra={
                "run_id": run_id,
                "data_type": data_type,
                "status": status.value,
            },
        )

    def get_data_status(
        self,
        run_id: str,
        data_type: str,
    ) -> DataStatus:
        """Get the status of specific data.

        Args:
            run_id: The run identifier
            data_type: Type of data

        Returns:
            Current status of the data
        """
        run_status = self._data_status.get(run_id, {})
        return run_status.get(data_type, DataStatus.VALID)

    def prepare_for_backtrack(
        self,
        run_id: str,
        from_stage: StageName,
        to_stage: StageName,
    ) -> dict:
        """Prepare for a backtracking operation.

        This method:
        1. Marks downstream data as pending validation
        2. Returns preserved data for the target stage

        Args:
            run_id: The run identifier
            from_stage: The current stage
            to_stage: The target stage

        Returns:
            Dictionary with preserved data and metadata
        """
        # Mark downstream data
        data_to_regenerate = self.get_data_to_regenerate(from_stage, to_stage)
        for data_type in data_to_regenerate:
            self.mark_data_status(run_id, data_type, DataStatus.PENDING_VALIDATION)

        # Get preserved data
        data_to_preserve = self.get_data_to_preserve(from_stage, to_stage)
        preserved: dict = {}

        if "topic" in data_to_preserve:
            run = self._repository.get_run(run_id)
            preserved["topic"] = run.topic
            preserved["constraints"] = run.constraints.model_dump()

        if "selected_papers" in data_to_preserve:
            papers = self._repository.load_selected_papers(run_id)
            preserved["selected_papers"] = [p.model_dump() for p in papers]

        if "evidence_cards" in data_to_preserve:
            cards = self._repository.load_evidence_cards(run_id)
            preserved["evidence_cards"] = [c.model_dump() for c in cards]

        self._logger.info(
            "Prepared for backtrack",
            extra={
                "run_id": run_id,
                "from": from_stage,
                "to": to_stage,
                "preserved_keys": list(preserved.keys()),
                "regenerate": data_to_regenerate,
            },
        )

        return preserved

    def get_stage_dependencies(self, stage_name: StageName) -> list[StageName]:
        """Get stages that the given stage depends on.

        Args:
            stage_name: The stage to check

        Returns:
            List of stages that must complete before this stage
        """
        dependencies: dict[StageName, list[StageName]] = {
            "retrieval": [],
            "review": ["retrieval"],
            "critic": ["retrieval", "review"],
            "planner": ["retrieval", "review", "critic"],
        }
        return dependencies.get(stage_name, [])

    def get_dependent_stages(self, stage_name: StageName) -> list[StageName]:
        """Get stages that depend on the given stage.

        Args:
            stage_name: The stage to check

        Returns:
            List of stages that require this stage to complete
        """
        dependent: dict[StageName, list[StageName]] = {
            "retrieval": ["review", "critic", "planner"],
            "review": ["critic", "planner"],
            "critic": ["planner"],
            "planner": [],
        }
        return dependent.get(stage_name, [])

    def clear_run_state(self, run_id: str) -> None:
        """Clear all tracked state for a run.

        Args:
            run_id: The run identifier
        """
        if run_id in self._data_status:
            del self._data_status[run_id]
