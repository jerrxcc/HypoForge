"""Evidence Validator Agent.

This module provides the EvidenceValidator agent that validates evidence cards
for completeness, accuracy, and relevance after the Review stage.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from hypoforge.agents.validation_base import ValidationAgent
from hypoforge.domain.validation import (
    ConflictHint,
    EvidenceValidationReport,
    InvalidEvidence,
    ValidationContext,
    ValidationIssue,
    ValidationResult,
)
from hypoforge.domain.schemas import StageName, Severity

if TYPE_CHECKING:
    from hypoforge.config import ValidationSettings
    from hypoforge.infrastructure.db.repository import RunRepository


logger = logging.getLogger(__name__)


# System prompt for evidence validation
EVIDENCE_VALIDATION_PROMPT = """You are an expert evidence validator for scientific research.

Your task is to evaluate evidence cards extracted from research papers and assess:
1. **Completeness**: Are all required fields present and meaningful?
2. **Accuracy**: Does the claim align with what could reasonably be derived from a paper abstract?
3. **Relevance**: Is the evidence relevant to the research topic?

For each evidence card, provide:
- A quality score (0.0-1.0)
- Any issues found
- Whether the evidence should be considered valid

Focus on identifying:
- Missing critical fields (system/material, intervention, outcome)
- Vague or uninformative claims
- Evidence that doesn't relate to the research topic
- Potential conflicts between evidence cards

Return your assessment as structured JSON with scores and issues for each evidence ID."""


class EvidenceValidator(ValidationAgent):
    """Validates evidence cards for quality and relevance.

    This validator runs after the Review stage to ensure evidence cards
    meet quality standards before they are used for conflict detection.

    Validation Dimensions:
    - Completeness: Required fields presence and quality
    - Accuracy: Claim consistency with expected paper content
    - Relevance: Semantic relevance to research topic
    - Conflict hints: Potential conflicts between evidence
    """

    def __init__(
        self,
        *,
        repository: RunRepository,
        settings: ValidationSettings,
        provider: Any | None = None,
    ) -> None:
        """Initialize the evidence validator.

        Args:
            repository: The run repository for loading data
            settings: Validation settings for thresholds
            provider: Optional LLM provider for enhanced validation
        """
        super().__init__(
            repository=repository,
            thresholds={
                "completeness": settings.evidence_completeness_threshold,
                "accuracy": settings.evidence_accuracy_threshold,
                "relevance": settings.evidence_relevance_threshold,
                "min_valid": settings.min_valid_evidence,
            },
            model_name=settings.model_evidence_validator,
        )
        self._settings = settings
        self._provider = provider

    @property
    def validation_type(self) -> str:
        return "evidence_validation"

    @property
    def target_stage(self) -> StageName:
        return "review"

    async def validate(self, context: ValidationContext) -> ValidationResult:
        """Validate evidence cards for the run.

        Args:
            context: Validation context with run data

        Returns:
            ValidationResult with evidence validation report
        """
        run_id = context.run_id
        topic = context.topic

        self._logger.info(
            "Starting evidence validation",
            extra={"run_id": run_id, "topic": topic},
        )

        # Load evidence cards
        evidence_cards = self._load_evidence_cards(run_id)

        if not evidence_cards:
            return self._create_empty_result(run_id)

        # Load papers for reference
        papers = self._load_selected_papers(run_id)
        paper_map = {p.paper_id: p for p in papers}

        # Validate each evidence card
        valid_ids: list[str] = []
        invalid_evidence: list[InvalidEvidence] = []
        conflict_hints: list[ConflictHint] = []
        quality_scores: dict[str, float] = {}

        for card in evidence_cards:
            score, issues = self._validate_single_card(
                card=card,
                paper=paper_map.get(card.paper_id),
                topic=topic,
            )

            quality_scores[card.evidence_id] = score

            if score >= self._thresholds["completeness"]:
                valid_ids.append(card.evidence_id)
            else:
                invalid_evidence.append(InvalidEvidence(
                    evidence_id=card.evidence_id,
                    reason="; ".join(issues) if issues else "Low quality score",
                    severity="medium" if score >= 0.4 else "high",
                    suggested_action=self._suggest_fix(card, issues),
                ))

        # Detect potential conflicts between evidence
        conflict_hints = self._detect_conflict_hints(evidence_cards)

        # Calculate aggregate scores
        completeness_score = self._calculate_completeness_score(evidence_cards)
        accuracy_score = self._calculate_accuracy_score(evidence_cards, paper_map)
        relevance_score = self._calculate_relevance_score(evidence_cards, topic)

        overall_score = (
            completeness_score * 0.35 +
            accuracy_score * 0.35 +
            relevance_score * 0.30
        )

        # Create validation report
        report = EvidenceValidationReport(
            valid_evidence_ids=valid_ids,
            invalid_evidence_ids=invalid_evidence,
            conflict_hints=conflict_hints,
            quality_scores=quality_scores,
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            relevance_score=relevance_score,
            overall_score=overall_score,
        )

        # Determine if valid
        valid_count = len(valid_ids)
        min_valid = self._thresholds["min_valid"]
        is_valid = valid_count >= min_valid and overall_score >= self._thresholds["completeness"]

        # Create issues list
        issues = self._create_issues_list(
            report=report,
            valid_count=valid_count,
            min_valid=min_valid,
        )

        # Determine backtrack recommendation
        backtrack = None
        if not is_valid:
            backtrack = self._determine_backtrack(
                report=report,
                valid_count=valid_count,
                min_valid=min_valid,
                context=context,
            )

        self._logger.info(
            "Evidence validation completed",
            extra={
                "run_id": run_id,
                "valid": is_valid,
                "score": overall_score,
                "valid_count": valid_count,
                "total_count": len(evidence_cards),
            },
        )

        return ValidationResult(
            valid=is_valid,
            score=overall_score,
            issues=issues,
            backtrack_recommendation=backtrack,
            validation_type=self.validation_type,
            validated_count=len(evidence_cards),
            passed_count=valid_count,
        )

    def _validate_single_card(
        self,
        card: Any,
        paper: Any | None,
        topic: str,
    ) -> tuple[float, list[str]]:
        """Validate a single evidence card.

        Args:
            card: The evidence card to validate
            paper: The source paper (if available)
            topic: The research topic

        Returns:
            Tuple of (quality score, list of issues)
        """
        issues: list[str] = []
        scores: list[float] = []

        # Check completeness
        completeness_score, completeness_issues = self._check_completeness(card)
        scores.append(completeness_score)
        issues.extend(completeness_issues)

        # Check accuracy (if paper available)
        if paper:
            accuracy_score, accuracy_issues = self._check_accuracy(card, paper)
            scores.append(accuracy_score)
            issues.extend(accuracy_issues)
        else:
            scores.append(0.5)  # Neutral if no paper

        # Check relevance
        relevance_score, relevance_issues = self._check_relevance(card, topic)
        scores.append(relevance_score)
        issues.extend(relevance_issues)

        # Calculate overall score
        overall_score = sum(scores) / len(scores) if scores else 0.0

        return overall_score, issues

    def _check_completeness(self, card: Any) -> tuple[float, list[str]]:
        """Check evidence card completeness."""
        issues: list[str] = []
        score = 1.0

        required_fields = [
            ("system_or_material", 0.15),
            ("intervention", 0.15),
            ("outcome", 0.15),
            ("claim_text", 0.10),
            ("direction", 0.05),
        ]

        for field_name, penalty in required_fields:
            value = getattr(card, field_name, None)
            if not value or (isinstance(value, str) and not value.strip()):
                issues.append(f"Missing or empty field: {field_name}")
                score -= penalty

        # Check claim quality
        if card.claim_text:
            claim_length = len(card.claim_text)
            if claim_length < 20:
                issues.append("Claim text is too short")
                score -= 0.10
            elif claim_length < 50:
                score -= 0.05

        # Check confidence
        if card.confidence < 0.3:
            issues.append("Very low confidence score")
            score -= 0.10

        return max(0.0, score), issues

    def _check_accuracy(self, card: Any, paper: Any) -> tuple[float, list[str]]:
        """Check evidence card accuracy against paper.

        Note: This is a heuristic check. Full accuracy validation
        would require LLM analysis.
        """
        issues: list[str] = []
        score = 1.0

        # Check if paper_id matches
        if card.paper_id != paper.paper_id:
            issues.append("Paper ID mismatch")
            score -= 0.30

        # Check title consistency (if card has title)
        if card.title and paper.title:
            # Simple check: card title should be related to paper title
            card_title_lower = card.title.lower()
            paper_title_lower = paper.title.lower()

            # Check for word overlap
            card_words = set(card_title_lower.split())
            paper_words = set(paper_title_lower.split())
            overlap = len(card_words & paper_words)

            if overlap < 2 and len(card_words) > 3:
                issues.append("Card title may not match paper")
                score -= 0.15

        # Check if abstract exists for grounding
        if not paper.abstract:
            issues.append("No abstract available for grounding")
            score -= 0.10

        return max(0.0, score), issues

    def _check_relevance(self, card: Any, topic: str) -> tuple[float, list[str]]:
        """Check evidence card relevance to topic.

        Note: This is a heuristic check. Full relevance validation
        would require embedding-based semantic similarity.
        """
        issues: list[str] = []
        score = 1.0

        topic_lower = topic.lower()
        topic_words = set(topic_lower.split())

        # Check claim text for topic keywords
        if card.claim_text:
            claim_lower = card.claim_text.lower()
            claim_words = set(claim_lower.split())

            # Check for topic word presence
            topic_overlap = len(topic_words & claim_words)
            if topic_overlap == 0:
                # Check for related terms
                related_terms = self._get_related_terms(topic)
                if not any(term in claim_lower for term in related_terms):
                    issues.append("Claim may not be relevant to topic")
                    score -= 0.20

        # Check system_or_material relevance
        if card.system_or_material:
            system_lower = card.system_or_material.lower()
            if not any(word in system_lower for word in topic_words):
                score -= 0.05  # Minor penalty

        return max(0.0, score), issues

    def _get_related_terms(self, topic: str) -> list[str]:
        """Get related terms for a topic.

        This is a simplified implementation. In production, this would
        use a domain-specific taxonomy or word embeddings.
        """
        # Common scientific term variations
        topic_lower = topic.lower()
        related = [topic_lower]

        # Add common suffixes
        suffixes = ["s", "es", "ing", "ed", "tion", "sion", "ment", "ness"]
        for suffix in suffixes:
            related.append(topic_lower + suffix)

        # Add domain-specific related terms
        # This would be expanded based on the research domain
        domain_terms = {
            "battery": ["electrolyte", "electrode", "cell", "energy", "storage"],
            "cancer": ["tumor", "oncology", "malignant", "therapy", "treatment"],
            "ai": ["machine learning", "neural", "deep learning", "model", "algorithm"],
        }

        for key, terms in domain_terms.items():
            if key in topic_lower:
                related.extend(terms)

        return related

    def _detect_conflict_hints(self, evidence_cards: list[Any]) -> list[ConflictHint]:
        """Detect potential conflicts between evidence cards.

        This identifies pairs of evidence that may have conflicting conclusions.
        """
        hints: list[ConflictHint] = []

        # Group evidence by topic axis (system/material)
        by_system: dict[str, list[Any]] = {}
        for card in evidence_cards:
            key = card.system_or_material.lower() if card.system_or_material else "unknown"
            if key not in by_system:
                by_system[key] = []
            by_system[key].append(card)

        # Look for conflicting directions within same system
        for system, cards in by_system.items():
            if len(cards) < 2:
                continue

            positive = [c for c in cards if c.direction == "positive"]
            negative = [c for c in cards if c.direction == "negative"]

            if positive and negative:
                # Found potential conflict
                hints.append(ConflictHint(
                    evidence_id_1=positive[0].evidence_id,
                    evidence_id_2=negative[0].evidence_id,
                    conflict_type="directional_conflict",
                    description=f"Conflicting directions for {system}: positive vs negative outcomes",
                    confidence=0.6,
                ))

        return hints

    def _calculate_completeness_score(self, evidence_cards: list[Any]) -> float:
        """Calculate aggregate completeness score."""
        if not evidence_cards:
            return 0.0

        scores = []
        for card in evidence_cards:
            score = 1.0
            required = ["system_or_material", "intervention", "outcome", "claim_text"]
            for field in required:
                value = getattr(card, field, None)
                if not value or (isinstance(value, str) and not value.strip()):
                    score -= 0.25
            scores.append(max(0.0, score))

        return sum(scores) / len(scores)

    def _calculate_accuracy_score(
        self,
        evidence_cards: list[Any],
        paper_map: dict[str, Any],
    ) -> float:
        """Calculate aggregate accuracy score."""
        if not evidence_cards:
            return 0.0

        scores = []
        for card in evidence_cards:
            paper = paper_map.get(card.paper_id)
            if paper:
                # Basic accuracy: paper exists and has abstract
                score = 0.7
                if paper.abstract:
                    score += 0.3
                scores.append(score)
            else:
                scores.append(0.3)  # Low score if paper not found

        return sum(scores) / len(scores)

    def _calculate_relevance_score(self, evidence_cards: list[Any], topic: str) -> float:
        """Calculate aggregate relevance score."""
        if not evidence_cards:
            return 0.0

        topic_words = set(topic.lower().split())
        scores = []

        for card in evidence_cards:
            if card.claim_text:
                claim_words = set(card.claim_text.lower().split())
                overlap = len(topic_words & claim_words)
                # Normalize by topic words
                score = min(1.0, overlap / max(1, len(topic_words)) * 2)
                scores.append(score)
            else:
                scores.append(0.0)

        return sum(scores) / len(scores) if scores else 0.0

    def _suggest_fix(self, card: Any, issues: list[str]) -> str:
        """Suggest a fix for invalid evidence."""
        if "Missing or empty field" in str(issues):
            return "Re-extract evidence with complete field coverage"
        if "too short" in str(issues):
            return "Expand claim text with more specific details"
        if "confidence" in str(issues).lower():
            return "Review source paper for stronger evidence"
        return "Re-evaluate evidence extraction from source paper"

    def _create_empty_result(self, run_id: str) -> ValidationResult:
        """Create a result for empty evidence."""
        return ValidationResult(
            valid=False,
            score=0.0,
            issues=[ValidationIssue(
                issue_type="no_evidence",
                severity="critical",
                description="No evidence cards found to validate",
                affected_ids=[],
                suggested_fix="Re-run review stage to extract evidence",
            )],
            backtrack_recommendation=self.create_backtrack_recommendation(
                target_stage="review",
                reason="No evidence cards available for validation",
                priority="critical",
                estimated_impact=0.8,
            ),
            validation_type=self.validation_type,
            validated_count=0,
            passed_count=0,
        )

    def _create_issues_list(
        self,
        report: EvidenceValidationReport,
        valid_count: int,
        min_valid: int,
    ) -> list[ValidationIssue]:
        """Create list of validation issues from report."""
        issues: list[ValidationIssue] = []

        # Add count issue if below threshold
        if valid_count < min_valid:
            issues.append(ValidationIssue(
                issue_type="insufficient_valid_evidence",
                severity="high" if valid_count < min_valid // 2 else "medium",
                description=f"Only {valid_count} valid evidence cards (minimum: {min_valid})",
                affected_ids=[],
                suggested_fix="Extract more evidence from papers or broaden paper selection",
            ))

        # Add issues for invalid evidence
        for invalid in report.invalid_evidence_ids[:5]:  # Limit to top 5
            issues.append(ValidationIssue(
                issue_type="invalid_evidence",
                severity=invalid.severity,
                description=f"Evidence {invalid.evidence_id}: {invalid.reason}",
                affected_ids=[invalid.evidence_id],
                suggested_fix=invalid.suggested_action,
            ))

        # Add conflict hints as issues
        for hint in report.conflict_hints[:3]:  # Limit to top 3
            issues.append(ValidationIssue(
                issue_type="potential_conflict",
                severity="low",
                description=hint.description,
                affected_ids=[hint.evidence_id_1, hint.evidence_id_2],
                suggested_fix="Review conflicting evidence during conflict analysis",
            ))

        return issues

    def _determine_backtrack(
        self,
        report: EvidenceValidationReport,
        valid_count: int,
        min_valid: int,
        context: ValidationContext,
    ) -> Any:
        """Determine backtrack recommendation."""
        from hypoforge.domain.validation import BacktrackRecommendation

        # Severe shortage: backtrack to retrieval for more papers
        if valid_count < min_valid // 2:
            return BacktrackRecommendation(
                target_stage="retrieval",
                reason=f"Severe evidence shortage ({valid_count}/{min_valid}). Need more papers.",
                priority="high",
                estimated_impact=0.7,
            )

        # Moderate shortage: backtrack to review for better extraction
        if valid_count < min_valid:
            return BacktrackRecommendation(
                target_stage="review",
                reason=f"Insufficient valid evidence ({valid_count}/{min_valid}). Re-extract with better coverage.",
                priority="medium",
                estimated_impact=0.5,
            )

        # Low quality: backtrack to review
        if report.overall_score < self._thresholds["completeness"]:
            return BacktrackRecommendation(
                target_stage="review",
                reason=f"Low evidence quality ({report.overall_score:.2f}). Improve extraction depth.",
                priority="medium",
                estimated_impact=0.4,
            )

        return None
