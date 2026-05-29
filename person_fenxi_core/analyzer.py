"""Analyzer module for multi-turn psychological analysis."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AnalysisStage(Enum):
    """Analysis progress stages."""

    GREETING = "greeting"  # 问候阶段
    COLLECTION = "collection"  # 信息收集
    ANALYSIS = "analysis"  # 分析执行
    FEEDBACK = "feedback"  # 反馈调整
    CONCLUSION = "conclusion"  # 结论总结


@dataclass
class AnalysisTurn:
    """Single turn in analysis conversation."""

    stage: AnalysisStage
    user_input: str
    assistant_response: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PsychProfile:
    """Psychological profile result."""

    # 五层分析结果
    behavior_layer: str = ""  # 行为层
    thinking_layer: str = ""  # 思维层
    relationship_layer: str = ""  # 关系层
    transition_layer: str = ""  # 转折层
    life_stage_layer: str = ""  # 人生阶段层

    # 综合信息
    core_pattern: list[str] = field(default_factory=list)
    confidence_scores: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "behavior_layer": self.behavior_layer,
            "thinking_layer": self.thinking_layer,
            "relationship_layer": self.relationship_layer,
            "transition_layer": self.transition_layer,
            "life_stage_layer": self.life_stage_layer,
            "core_pattern": self.core_pattern,
            "confidence_scores": self.confidence_scores,
        }


class Analyzer:
    """Multi-turn psychological analyzer using LLM."""

    SYSTEM_PROMPT = """你是一位专业的心理咨询师，使用陈海贤《了不起的我》中的五层分析法框架。

五层分析法：
1. 行为层 - 分析想不想改变，什么在阻止改变
2. 思维层 - 分析心智模式（成长型/防御型）
3. 关系层 - 分析关系中的角色和依恋类型
4. 转折层 - 分析人生转折阶段
5. 人生阶段层 - 分析当前人生阶段和课题

分析原则：
- 先观察用户提供的素材，提取具体表现
- 对照理论框架匹配类型
- 输出结论时要说明置信度
- 提供可操作的对话镜片"""

    def __init__(
        self,
        llm_client,
        vector_store=None,
        num_rounds: int = 5,
    ) -> None:
        self.llm_client = llm_client
        self.vector_store = vector_store
        self.num_rounds = num_rounds

    def analyze(
        self,
        user_input: str,
        context: dict[str, Any] | None = None,
    ) -> tuple[str, PsychProfile]:
        """Analyze user input and return response + profile.

        Args:
            user_input: User's message
            context: Optional context dict with previous data

        Returns:
            Tuple of (assistant_response, psych_profile)
        """
        # Build messages
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_input},
        ]

        # Add context if available
        if context and context.get("materials"):
            materials_prompt = f"\n\n用户素材：\n{context['materials']}"
            messages[-1]["content"] += materials_prompt

        # Query relevant knowledge if vector store available
        if self.vector_store:
            context_docs = self._retrieve_context(user_input)
            if context_docs:
                context_prompt = f"\n\n参考知识：\n{context_docs}"
                messages.insert(1, {"role": "system", "content": context_prompt})

        # Get LLM response
        response = self.llm_client.chat_completion(messages)

        # Parse into profile (simplified - in production use structured output)
        profile = self._parse_profile(response.content)

        return response.content, profile

    def _retrieve_context(self, query: str) -> str | None:
        """Retrieve relevant context from vector store."""
        if not self.vector_store:
            return None

        # Get embedding for query
        query_emb = self.llm_client.get_embedding(query)

        # Search
        results = self.vector_store.search(query_emb, k=3)

        if not results:
            return None

        # Format context
        docs = []
        for doc_id, distance, payload, _ in results:
            if payload and "text" in payload:
                docs.append(f"- {payload['text']}")

        return "\n".join(docs) if docs else None

    def _parse_profile(self, llm_output: str) -> PsychProfile:
        """Parse LLM output into PsychProfile."""
        profile = PsychProfile()

        # Simplified parsing - in production use structured output
        lines = llm_output.split("\n")
        current_layer = ""

        for line in lines:
            if "行为层" in line:
                current_layer = "behavior_layer"
            elif "思维层" in line:
                current_layer = "thinking_layer"
            elif "关系层" in line:
                current_layer = "relationship_layer"
            elif "转折层" in line:
                current_layer = "transition_layer"
            elif "人生阶段" in line:
                current_layer = "life_stage_layer"
            elif current_layer and line.strip().startswith("-"):
                setattr(profile, current_layer, line.strip()[1:].strip())

        return profile


# Convenience function
def create_analyzer(llm_client, vector_store=None) -> Analyzer:
    """Create analyzer instance."""
    return Analyzer(llm_client=llm_client, vector_store=vector_store)