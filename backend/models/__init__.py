"""Data models for Relation Warning System."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class RiskLevel(Enum):
    """Risk level enumeration."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Speaker(Enum):
    """Speaker roles in dialogue."""

    ME = "我"      # 自己
    THEM = "对方"    # 对方


class ColorType(Enum):
    """Four color personality types."""

    RED = "红色"    # 情感驱动
    BLUE = "蓝色"    # 逻辑驱动
    YELLOW = "黄色"  # 目标驱动
    GREEN = "绿色"   # 和平驱动


@dataclass
class Message:
    """Single message in dialogue."""

    turn: int              # Turn number (1-indexed)
    speaker: str           # "我" or "对方"
    content: str           # Message content
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self) -> None:
        """Validate speaker is valid."""
        if self.speaker not in ["我", "对方"]:
            raise ValueError(f"Invalid speaker: {self.speaker}. Must be '我' or '对方'.")


@dataclass
class ConflictSignal:
    """Detected conflict signal in dialogue."""

    turn: int              # Which turn triggered this
    speaker: str           # Who said the triggering message
    message: str           # The message content
    conflict_type: str       # Pattern name, e.g., "blue_logic_pressure"
    risk_level: str         # "high" | "medium" | "low"
    reason: str            # Why this is a conflict, Chinese explanation
    suggestion: str = ""     # How to respond, optional

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "turn": self.turn,
            "speaker": self.speaker,
            "message": self.message,
            "type": self.conflict_type,
            "risk_level": self.risk_level,
            "reason": self.reason,
            "suggestion": self.suggestion,
        }


@dataclass
class AnalysisResult:
    """Complete analysis result."""

    signals: list[ConflictSignal] = field(default_factory=list)
    risk_index: float = 0.0        # 0-100 risk score
    summary: str = ""               # Summary in Chinese
    dialogue_length: int = 0          # Number of turns

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "signals": [s.to_dict() for s in self.signals],
            "risk_index": self.risk_index,
            "summary": self.summary,
            "dialogue_length": self.dialogue_length,
        }


@dataclass
class AnalysisRequest:
    """Request for analysis API."""

    dialogue: list[Message]
    my_color: str = ""           # My color type
    their_color: str = ""        # Their color type

    def __post_init__(self) -> None:
        """Ensure dialogue is list of Message."""
        if not self.dialogue:
            raise ValueError("Dialogue cannot be empty")