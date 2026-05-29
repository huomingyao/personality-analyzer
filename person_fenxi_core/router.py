"""Router module for intent recognition and dispatch."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable


class Intent(Enum):
    """Supported user intents."""

    ANALYZE_PSYCHE = "analyze_psyche"  # 心理分析
    QUERY_KNOWLEDGE = "query_knowledge"  # 知识查询
    UPGRADE_SKILL = "upgrade_skill"  # 技能升级
    START_SESSION = "start_session"  # 开始新会话
    CONTINUE_SESSION = "continue_session"  # 继续会话
    UNKNOWN = "unknown"


# Intent keywords mapping
INTENT_KEYWORDS: dict[Intent, tuple[str, ...]] = {
    Intent.ANALYZE_PSYCHE: (
        "分析",
        "心理",
        "心智模式",
        "行为模式",
        "转折期",
        "依恋类型",
        "人格",
        "性格",
        "、自我认知",
    ),
    Intent.QUERY_KNOWLEDGE: (
        "什么是",
        "怎么",
        "如何",
        "解释",
        "原理",
        "理论",
        "案例",
    ),
    Intent.UPGRADE_SKILL: (
        "升级",
        "增强",
        "添加",
        "新功能",
    ),
    Intent.START_SESSION: (
        "新会话",
        "从头开始",
        "重新开始",
    ),
}


@dataclass
class RoutingResult:
    """Result from router."""

    intent: Intent
    confidence: float  # 0.0 - 1.0
    target_handler: str  # Handler module/class name


class Router:
    """Intent router forPsyche KB."""

    def __init__(self, llm_client=None) -> None:
        self.llm_client = llm_client
        self._keyword_cache: dict[str, Intent] = {}

    def route(self, user_input: str) -> RoutingResult:
        """Route user input to appropriate handler.

        Args:
            user_input: Raw user input text

        Returns:
            RoutingResult with intent, confidence, and handler info
        """
        # First try keyword matching
        intent, confidence = self._match_keywords(user_input)

        # If low confidence, try LLM classification
        if confidence < 0.5 and self.llm_client:
            intent, confidence = self._llm_classify(user_input)

        # Fallback to unknown
        if intent == Intent.UNKNOWN:
            intent = Intent.ANALYZE_PSYCHE  # Default to analyze
            confidence = 0.3

        handler = self._get_handler(intent)

        return RoutingResult(
            intent=intent,
            confidence=confidence,
            target_handler=handler,
        )

    def _match_keywords(self, text: str) -> tuple[Intent, float]:
        """Match intent using keywords."""
        text_lower = text.lower()

        best_intent = Intent.UNKNOWN
        best_score = 0.0

        for intent, keywords in INTENT_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > best_score:
                best_score = score
                best_intent = intent

        # Normalize confidence
        confidence = min(best_score / 2.0, 1.0)

        return best_intent, confidence

    def _llm_classify(self, text: str) -> tuple[Intent, float]:
        """Use LLM for intent classification."""
        # Placeholder for LLM-based classification
        # In production, prompt LLM to classify
        return Intent.UNKNOWN, 0.0

    def _get_handler(self, intent: Intent) -> str:
        """Get handler module name for intent."""
        handler_map = {
            Intent.ANALYZE_PSYCHE: "src.analyzer",
            Intent.QUERY_KNOWLEDGE: "src.storage.vector_store",
            Intent.UPGRADE_SKILL: "src.corpus2skill.pipeline",
            Intent.START_SESSION: "src.session",
            Intent.CONTINUE_SESSION: "src.session",
            Intent.UNKNOWN: "src.analyzer",
        }
        return handler_map.get(intent, "src.analyzer")


def route_user_input(user_input: str) -> RoutingResult:
    """Convenience function for routing."""
    router = Router()
    return router.route(user_input)