"""Conflict analyzer engine."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from backend.models import (
    AnalysisResult,
    ConflictSignal,
    Message,
)
from conflict_patterns import (
    CONFLICT_PATTERNS,
    ESCALATION_SIGNALS,
    WITHDRAWAL_SIGNALS,
    get_patterns_for_interaction,
)


class ConflictAnalyzer:
    """Core conflict detection engine."""

    def __init__(self) -> None:
        self.patterns = CONFLICT_PATTERNS

    def analyze(
        self,
        dialogue: list[dict[str, Any]],
        my_color: str = "",
        their_color: str = "",
    ) -> AnalysisResult:
        """Analyze dialogue for conflict signals.

        Args:
            dialogue: List of message dicts with keys: turn, speaker, content
            my_color: My color type (红/蓝/黄/绿)
            their_color: Their color type

        Returns:
            AnalysisResult with signals and risk index
        """
        # Convert to Message objects
        messages = [
            Message(
                turn=m.get("turn", i + 1),
                speaker=m.get("speaker", ""),
                content=m.get("content", ""),
            )
            for i, m in enumerate(dialogue)
        ]

        # Detect signals
        signals = self._detect_signals(messages, my_color, their_color)

        # Compute risk index
        risk_index = self._compute_risk_index(signals, messages)

        # Generate summary
        summary = self._generate_summary(signals, risk_index)

        return AnalysisResult(
            signals=signals,
            risk_index=risk_index,
            summary=summary,
            dialogue_length=len(messages),
        )

    def _detect_signals(
        self,
        messages: list[Message],
        my_color: str,
        their_color: str,
    ) -> list[ConflictSignal]:
        """Detect conflict signals in dialogue."""
        signals = []

        # Get relevant patterns
        relevant_patterns = get_patterns_for_interaction(
            my_color or "蓝色",  # Default fallback
            their_color or "红色",
        )

        for msg in messages:
            if not msg.content:
                continue

            # Check patterns
            for pattern in relevant_patterns:
                triggered = self._check_pattern(msg.content, pattern.trigger_patterns)
                if triggered:
                    signals.append(ConflictSignal(
                        turn=msg.turn,
                        speaker=msg.speaker,
                        message=msg.content,
                        conflict_type=pattern.name,
                        risk_level=pattern.risk_level,
                        reason=pattern.feel_when_triggered,
                        suggestion=", ".join(pattern.counter_suggestions[:2]) if pattern.counter_suggestions else "",
                    ))
                    # One signal per message maximum
                    break

            # Check withdrawal signals
            if self._check_withdrawal(msg.content):
                signals.append(ConflictSignal(
                    turn=msg.turn,
                    speaker=msg.speaker,
                    message=msg.content,
                    conflict_type="emotional_withdrawal",
                    risk_level="high",
                    reason="对方选择回避，可能已经产生防御心理",
                    suggestion="暂停争论，先修复关系",
                ))

            # Check escalation
            if self._check_escalation(msg.content):
                signals.append(ConflictSignal(
                    turn=msg.turn,
                    speaker=msg.speaker,
                    message=msg.content,
                    conflict_type="escalation_detected",
                    risk_level="high",
                    reason="对话升级，出现指责性语言",
                    suggestion="降温，聚焦具体事情",
                ))

        return signals

    def _check_pattern(self, content: str, triggers: list[str]) -> bool:
        """Check if content matches any trigger."""
        content_lower = content.lower()
        for trigger in triggers:
            if trigger.lower() in content_lower:
                return True
        return False

    def _check_withdrawal(self, content: str) -> bool:
        """Check if content indicates withdrawal."""
        for signal in WITHDRAWAL_SIGNALS:
            if signal in content:
                return True
        return False

    def _check_escalation(self, content: str) -> bool:
        """Check if content indicates escalation."""
        for signal in ESCALATION_SIGNALS:
            if signal in content:
                return True
        return False

    def _compute_risk_index(
        self,
        signals: list[ConflictSignal],
        messages: list[Message],
    ) -> float:
        """Compute overall risk index (0-100)."""
        if not signals or not messages:
            return 0.0

        # Base: signal count ratio
        signal_count = len(signals)
        msg_count = len(messages)
        base_score = (signal_count / msg_count) * 30

        # Weight by risk levels
        risk_weight = 0.0
        for signal in signals:
            if signal.risk_level == "high":
                risk_weight += 25
            elif signal.risk_level == "medium":
                risk_weight += 15
            else:
                risk_weight += 5

        # Cap at 100
        total = min(100.0, base_score + risk_weight)
        return round(total, 1)

    def _generate_summary(
        self,
        signals: list[ConflictSignal],
        risk_index: float,
    ) -> str:
        """Generate Chinese summary."""
        if not signals:
            return "对话氛围良好，未检测到明显冲突。"

        high_count = sum(1 for s in signals if s.risk_level == "high")
        medium_count = sum(1 for s in signals if s.risk_level == "medium")

        if risk_index >= 70:
            return f"检测到高风险冲突！已发现 {high_count} 处高风险信号，建议暂停争论，先修复关系。"
        elif risk_index >= 40:
            return f"检测到中等风险，存在 {medium_count} 处潜在冲突点，注意沟通方式。"
        else:
            return f"发现 {len(signals)} 处小摩擦，保持当前沟通方式即可。"

    def quick_check(
        self,
        message: str,
        my_color: str,
        their_color: str,
    ) -> ConflictSignal | None:
        """Quickly check a single message.

        Used for real-time plugin.
        """
        msg = Message(turn=1, speaker="", content=message)
        signals = self._detect_signals([msg], my_color, their_color)
        return signals[0] if signals else None


# Convenience function
def create_analyzer() -> ConflictAnalyzer:
    """Create analyzer instance."""
    return ConflictAnalyzer()


def quick_analyze(
    dialogue: list[dict[str, Any]],
    my_color: str = "",
    their_color: str = "",
) -> dict[str, Any]:
    """Quick analysis function.

    Usage:
        result = quick_analyze([
            {"turn": 1, "speaker": "我", "content": "你在干嘛？"},
            {"turn": 2, "speaker": "对方", "content": "没干嘛"},
        ], my_color="蓝色", their_color="红色")
    """
    analyzer = create_analyzer()
    result = analyzer.analyze(dialogue, my_color, their_color)
    return result.to_dict()