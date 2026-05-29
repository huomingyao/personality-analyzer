"""Critic module for skill quality review."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class IssueSeverity(Enum):
    """Severity levels for skill bugs."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class SkillIssue:
    """Issue discovered in skill definition."""

    issue_id: str
    severity: IssueSeverity
    category: str  # "completeness" | "consistency" | "usability"
    description: str
    location: str  # e.g., "line 42" or "SKILL.md:trigger"
    suggestion: str


@dataclass
class ReviewResult:
    """Result of skill review."""

    skill_id: str
    issues: list[SkillIssue] = field(default_factory=list)
    score: float = 0.0  # 0.0 - 1.0

    @property
    def has_errors(self) -> bool:
        """Check if any errors found."""
        return any(i.severity == IssueSeverity.ERROR for i in self.issues)

    @property
    def error_count(self) -> int:
        """Count errors."""
        return sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        """Count warnings."""
        return sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)


class SkillCritic:
    """Review skill definitions for quality issues."""

    def __init__(self) -> None:
        self.issue_counter = 0

    def review_skill(
        self,
        skill_dir: Path,
        skill_id: str | None = None,
    ) -> ReviewResult:
        """Review a skill definition.

        Args:
            skill_dir: Path to skill directory
            skill_id: Optional skill identifier

        Returns:
            ReviewResult with issues found
        """
        skill_id = skill_id or skill_dir.name

        # Find SKILL.md or equivalent
        skill_file = self._find_skill_file(skill_dir)
        if not skill_file:
            return ReviewResult(
                skill_id=skill_id,
                issues=[SkillIssue(
                    issue_id="MISSING_SKILL_FILE",
                    severity=IssueSeverity.ERROR,
                    category="completeness",
                    description="No SKILL.md or README.md found",
                    location=str(skill_dir),
                    suggestion="Add SKILL.md or README.md",
                )],
                score=0.0,
            )

        # Read content
        content = skill_file.read_text(encoding="utf-8")

        # Run checks
        issues = []
        issues.extend(self._check_frontmatter(content, skill_file.name))
        issues.extend(self._check_trigger(content, skill_file.name))
        issues.extend(self._check_structure(content, skill_file.name))
        issues.extend(self._check_examples(content, skill_file.name))

        # Calculate score
        score = self._calculate_score(issues)

        return ReviewResult(skill_id=skill_id, issues=issues, score=score)

    def _find_skill_file(self, skill_dir: Path) -> Path | None:
        """Find primary skill definition file."""
        for name in ["SKILL.md", "README.md"]:
            path = skill_dir / name
            if path.exists():
                return path

        # Check subdirectories
        for subdir in skill_dir.rglob("*"):
            if subdir.is_file() and subdir.name in ["SKILL.md", "README.md"]:
                return subdir

        return None

    def _check_frontmatter(
        self,
        content: str,
        filename: str,
    ) -> list[SkillIssue]:
        """Check frontmatter completeness."""
        issues = []

        # Check for required fields
        if not re.search(r"^---\s*\n.*?name:", content, re.MULTILINE):
            issues.append(SkillIssue(
                issue_id=self._next_id(),
                severity=IssueSeverity.WARNING,
                category="completeness",
                description="Missing 'name' field in frontmatter",
                location=f"{filename}:frontmatter",
                suggestion="Add 'name: <skill-name>' to frontmatter",
            ))

        if not re.search(r"^---\s*\n.*?description:", content, re.MULTILINE):
            issues.append(SkillIssue(
                issue_id=self._next_id(),
                severity=IssueSeverity.WARNING,
                category="completeness",
                description="Missing 'description' field",
                location=f"{filename}:frontmatter",
                suggestion="Add 'description: <description>'",
            ))

        return issues

    def _check_trigger(
        self,
        content: str,
        filename: str,
    ) -> list[SkillIssue]:
        """Check trigger definition."""
        issues = []

        has_trigger = bool(re.search(r"^trigger:", content, re.MULTILINE | re.IGNORECASE))
        has_trigger_field = bool(re.search(r"^trigger\s*:", content, re.MULTILINE | re.IGNORECASE))

        if not (has_trigger or has_trigger_field):
            issues.append(SkillIssue(
                issue_id=self._next_id(),
                severity=IssueSeverity.INFO,
                category="usability",
                description="No trigger field defined",
                location=f"{filename}:frontmatter",
                suggestion="Add 'trigger: <keywords>' to define activation",
            ))

        return issues

    def _check_structure(
        self,
        content: str,
        filename: str,
    ) -> list[SkillIssue]:
        """Check section structure."""
        issues = []

        # Check for required sections
        required_sections = ["## ", "### "]
        has_headers = any(re.search(pat, content) for pat in required_sections)

        if not has_headers:
            issues.append(SkillIssue(
                issue_id=self._next_id(),
                severity=IssueSeverity.WARNING,
                category="structure",
                description="No section headers found",
                location=filename,
                suggestion="Add ## Section headers for organization",
            ))

        return issues

    def _check_examples(
        self,
        content: str,
        filename: str,
    ) -> list[SkillIssue]:
        """Check examples section."""
        issues = []

        has_examples = bool(re.search(r"## .*[Ee]xamples?", content))

        if not has_examples:
            issues.append(SkillIssue(
                issue_id=self._next_id(),
                severity=IssueSeverity.INFO,
                category="completeness",
                description="No Examples section found",
                location=filename,
                suggestion="Add ## Examples section with usage",
            ))

        return issues

    def _calculate_score(self, issues: list[SkillIssue]) -> float:
        """Calculate quality score (0.0 - 1.0)."""
        if not issues:
            return 1.0

        # Start with 1.0, deduct for issues
        score = 1.0
        for issue in issues:
            if issue.severity == IssueSeverity.ERROR:
                score -= 0.2
            elif issue.severity == IssueSeverity.WARNING:
                score -= 0.1
            else:  # INFO
                score -= 0.05

        return max(0.0, score)

    def _next_id(self) -> str:
        """Generate next issue ID."""
        self.issue_counter += 1
        return f"ISSUE_{self.issue_counter:03d}"


# Convenience function
def review_skill(skill_dir: Path) -> ReviewResult:
    """Review a skill definition."""
    critic = SkillCritic()
    return critic.review_skill(skill_dir)