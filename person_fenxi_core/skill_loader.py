"""Skill loader - dynamic loading of external skills."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from src.config import DATA_DIR


# Skills directory - project root skills/
GLOBAL_SKILLS_DIR = Path(__file__).parent.parent / "skills"


@dataclass
class LoadedSkill:
    """Loaded external skill."""

    skill_id: str
    name: str
    description: str
    trigger_keywords: list[str]
    content: str  # Full skill content
    prompt_template: str  # Formatted prompt for LLM
    version: str = "v1"
    source_path: Path | None = None


class SkillLoader:
    """Dynamic skill loader from external directories."""

    def __init__(self, skills_base_dir: Path | None = None) -> None:
        self.skills_base_dir = skills_base_dir or GLOBAL_SKILLS_DIR
        self._loaded_skills: dict[str, LoadedSkill] = {}

    def load_skill(
        self,
        skill_path: Path,
        skill_id: str | None = None,
    ) -> LoadedSkill | None:
        """Load skill from directory or SKILL.md file.

        Args:
            skill_path: Path to skill directory or SKILL.md file
            skill_id: Optional skill identifier

        Returns:
            Loaded skill or None if failed
        """
        # Resolve path
        if skill_path.is_dir():
            skill_file = skill_path / "SKILL.md"
            if not skill_file.exists():
                skill_file = skill_path / "README.md"
        elif skill_path.is_file():
            skill_file = skill_path
            skill_path = skill_path.parent
        else:
            return None

        # Read content
        content = skill_file.read_text(encoding="utf-8")

        # Parse frontmatter
        fm = self._parse_frontmatter(content)
        if not fm:
            return None

        skill_id = skill_id or fm.get("name", skill_path.name)

        # Extract trigger keywords
        triggers = self._extract_triggers(fm, content)

        # Build prompt template
        prompt_template = self._build_prompt_template(fm, content)

        skill = LoadedSkill(
            skill_id=skill_id,
            name=fm.get("name", skill_id),
            description=fm.get("description", ""),
            trigger_keywords=triggers,
            content=content,
            prompt_template=prompt_template,
            source_path=skill_path,
        )

        self._loaded_skills[skill_id] = skill
        return skill

    def load_skill_by_name(self, skill_name: str) -> LoadedSkill | None:
        """Load skill by name (directory name)."""
        skill_path = self.skills_base_dir / skill_name

        if not skill_path.exists():
            # Try global skills
            skill_path = GLOBAL_SKILLS_DIR / skill_name

        if not skill_path.exists():
            return None

        return self.load_skill(skill_path, skill_name)

    def register_handler(
        self,
        skill_id: str,
        handler: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        """Register execution handler for skill."""
        skill = self._loaded_skills.get(skill_id)
        if skill:
            # Store handler reference (can't serialize, but useful for type hints)
            pass

    def get_skill(self, skill_id: str) -> LoadedSkill | None:
        """Get loaded skill by ID."""
        return self._loaded_skills.get(skill_id)

    def find_skills_by_trigger(self, text: str) -> list[LoadedSkill]:
        """Find skills matching trigger text."""
        text_lower = text.lower()
        matches = []

        for skill in self._loaded_skills.values():
            for trigger in skill.trigger_keywords:
                if trigger.lower() in text_lower:
                    matches.append(skill)
                    break

        return matches

    def list_loaded_skills(self) -> list[dict[str, Any]]:
        """List all loaded skills."""
        return [
            {
                "skill_id": s.skill_id,
                "name": s.name,
                "description": s.description[:100] + "...",
                "trigger_count": len(s.trigger_keywords),
                "version": s.version,
            }
            for s in self._loaded_skills.values()
        ]

    def _parse_frontmatter(self, content: str) -> dict[str, str] | None:
        """Parse YAML frontmatter."""
        match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL | re.MULTILINE)
        if not match:
            return None

        fm = {}
        for line in match.group(1).split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                fm[key.strip()] = value.strip()

        return fm

    def _extract_triggers(
        self,
        fm: dict[str, str],
        content: str,
    ) -> list[str]:
        """Extract trigger keywords."""
        triggers = []

        # From frontmatter
        trigger_str = fm.get("trigger", "")
        if trigger_str:
            triggers.extend([t.strip() for t in trigger_str.split("/")])

        # From description field looking for trigger: keyword
        trigger_match = re.search(
            r"trigger[:\s]+([^\n\.]+)",
            content,
            re.IGNORECASE,
        )
        if trigger_match:
            extra = [t.strip() for t in trigger_match.group(1).split(",")]
            triggers.extend(extra)

        # Default: use name as trigger
        if not triggers and fm.get("name"):
            triggers.append(fm["name"])

        return list(set(triggers))  # Deduplicate

    def _build_prompt_template(
        self,
        fm: dict[str, str],
        content: str,
    ) -> str:
        """Build prompt template from skill content."""
        # Remove frontmatter for prompt
        content_no_fm = re.sub(
            r"^---\s*\n.*?\n---",
            "",
            content,
            count=1,
            flags=re.DOTALL | re.MULTILINE,
        ).strip()

        # Add name and description context
        template = f"""# Skill: {fm.get('name', 'Unknown')}
{fm.get('description', '')}

## 技能定义
{content_no_fm}

---

请基于上述技能定义进行分析。"""

        return template


# === Convenience Functions ===

def load_global_skill(skill_name: str) -> LoadedSkill | None:
    """Load a global skill by name."""
    loader = SkillLoader()
    return loader.load_skill_by_name(skill_name)


def find_matching_skills(text: str) -> list[dict[str, Any]]:
    """Find skills matching input text."""
    loader = SkillLoader()

    # Try to load common skills
    for skill_name in ["liangebodwo-mirror", "color_human"]:
        try:
            loader.load_skill_by_name(skill_name)
        except Exception:
            pass

    # Find matches
    matches = loader.find_skills_by_trigger(text)
    return [
        {
            "skill_id": s.skill_id,
            "name": s.name,
            "trigger": s.trigger_keywords[:3],
        }
        for s in matches
    ]