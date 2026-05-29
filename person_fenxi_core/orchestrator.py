"""Dual Agent Orchestrator - Analyzer ↔ Critic Loop."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from src.analyzer import Analyzer, PsychProfile
from src.critic import SkillCritic, ReviewResult
from src.router import Intent


class Decision(Enum):
    """Critic decision for next action."""

    CONTINUE = "continue"  # 需要继续分析
    STOP = "stop"  # 分析足够，可以停止
    CONFIRM = "confirm"  # 需要用户确认


@dataclass
class AgentTurn:
    """Single turn in dual-agent loop."""

    agent: str  # "analyzer" | "critic"
    input_text: str
    output_text: str
    decision: Decision | None = None


@dataclass
class AnalysisCycle:
    """Complete analysis cycle result."""

    target: str  # 被分析的对象
    rounds: int
    turns: list[AgentTurn] = field(default_factory=list)
    final_profile: PsychProfile | None = None
    skill_bugs: list[dict[str, Any]] = field(default_factory=list)
    concluded: bool = False
    conclusion_reason: str = ""


class DualAgentOrchestrator:
    """Orchestrate Analyzer ↔ Critic loop."""

    # 默认收敛条件
    MAX_ROUNDS = 5
    MIN_CONFIDENCE = 0.8

    def __init__(
        self,
        analyzer: Analyzer,
        critic_prompt_fn: Callable[[str, PsychProfile], tuple[str, Decision]],
        max_rounds: int = MAX_ROUNDS,
        min_confidence: float = MIN_CONFIDENCE,
    ) -> None:
        self.analyzer = analyzer
        self.critic_prompt_fn = critic_prompt_fn
        self.max_rounds = max_rounds
        self.min_confidence = min_confidence
        self._cycle_history: list[AnalysisCycle] = []

    def run_analysis(
        self,
        target: str,
        user_context: str,
        initial_materials: str | None = None,
    ) -> AnalysisCycle:
        """Run dual-agent analysis loop.

        Args:
            target: 被分析对象名称
            user_context: 用户提供的上下文/问题
            initial_materials: 可选的初始素材

        Returns:
            AnalysisCycle with complete results
        """
        cycle = AnalysisCycle(target=target, rounds=0)

        # 第1轮：Analyzer 初始分析
        context = {
            "target": target,
            "materials": initial_materials or "",
            "round": 1,
        }

        analyzer_output, profile = self.analyzer.analyze(
            user_context,
            context=context,
        )

        # 记录 Analyzer turn
        cycle.turns.append(AgentTurn(
            agent="analyzer",
            input_text=user_context,
            output_text=analyzer_output,
        ))

        # Critic 评估
        critic_feedback, decision = self.critic_prompt_fn(
            analyzer_output,
            profile,
        )

        # 记录 Critic turn
        cycle.turns.append(AgentTurn(
            agent="critic",
            input_text=analyzer_output,
            output_text=critic_feedback,
            decision=decision,
        ))

        cycle.rounds = 1
        cycle.final_profile = profile

        # 循环直到收敛
        while decision == Decision.CONTINUE and cycle.rounds < self.max_rounds:
            cycle = self._continue_analysis(
                cycle,
                user_context,
                critic_feedback,
            )

            # 下一轮 Critic 评估
            if cycle.final_profile:
                critic_feedback, decision = self.critic_prompt_fn(
                    self._get_latest_analyzer_output(cycle),
                    cycle.final_profile,
                )

                cycle.turns.append(AgentTurn(
                    agent="critic",
                    input_text=self._get_latest_analyzer_output(cycle),
                    output_text=critic_feedback,
                    decision=decision,
                ))

        # 设置最终结论
        if decision == Decision.STOP:
            cycle.concluded = True
            cycle.conclusion_reason = "critic确认分析足够深入"
        elif decision == Decision.CONFIRM:
            cycle.concluded = True
            cycle.conclusion_reason = "需要用户确认"
        elif cycle.rounds >= self.max_rounds:
            cycle.concluded = True
            cycle.conclusion_reason = "达到最大轮次"

        self._cycle_history.append(cycle)
        return cycle

    def _continue_analysis(
        self,
        cycle: AnalysisCycle,
        user_context: str,
        critic_feedback: str,
    ) -> AnalysisCycle:
        """Continue analysis with Critic feedback."""
        cycle.rounds += 1

        # 构建下一轮分析上下文
        context = {
            "target": cycle.target,
            "user_context": user_context,
            "critic_feedback": critic_feedback,
            "round": cycle.rounds,
            "previous_profile": cycle.final_profile.to_dict()
                if cycle.final_profile else {},
        }

        # Analyzer 下一轮
        analyzer_prompt = f"{user_context}\n\nCritic反馈：{critic_feedback}"
        analyzer_output, profile = self.analyzer.analyze(
            analyzer_prompt,
            context=context,
        )

        cycle.turns.append(AgentTurn(
            agent="analyzer",
            input_text=critic_feedback,
            output_text=analyzer_output,
        ))

        cycle.final_profile = profile

        return cycle

    def _get_latest_analyzer_output(self, cycle: AnalysisCycle) -> str:
        """Get most recent analyzer output."""
        for turn in reversed(cycle.turns):
            if turn.agent == "analyzer":
                return turn.output_text
        return ""

    def get_cycle_history(self) -> list[AnalysisCycle]:
        """Get previous analysis cycles."""
        return self._cycle_history


# === Critic Prompt Functions ===

def default_critic_prompt(
    analyzer_output: str,
    profile: PsychProfile,
) -> tuple[str, Decision]:
    """Default Critic prompt with 9-direction质疑框架.

    9方向质疑框架：
    1. 证据充分性 - 有足够证据支持结论吗？
    2. 逻辑一致性 - 各层分析逻辑自洽吗？
    3. 动机合理性 - 推断的动机合理吗？
    4. 情境依赖性 - 是否考虑了情境因素？
    5. 极端化倾向 - 是否过度概括/绝对化？
    6. 反例考虑 - 有没有考虑反例？
    7. 动机层级 - 分析了表面/深层动机吗？
    8. 变化可能 - 是否考虑改变的可能性？
    9. 盲点识别 - 是否有遗漏的重要维度？
    """
    issues = []

    # 1. 检查置信度
    conf_scores = profile.confidence_scores
    if conf_scores:
        avg_conf = sum(conf_scores.values()) / len(conf_scores)
        if avg_conf < 0.5:
            issues.append("置信度偏低，需要更多证据")

    # 2. 检查各层是否完备
    if not profile.behavior_layer:
        issues.append("缺少行为层分析")
    if not profile.thinking_layer:
        issues.append("缺少思维层分析")
    if not profile.relationship_layer:
        issues.append("缺少关系层分析")

    # 3. 检查核心模式
    if not profile.core_pattern:
        issues.append("缺少核心模式总结")

    # 生成反馈
    if issues:
        feedback = "需要继续分析：\n" + "\n".join(f"- {i}" for i in issues)
        return feedback, Decision.CONTINUE

    # 检查是否需要用户确认
    if len(profile.core_pattern) >= 2:
        return "分析较完整，建议用户确认", Decision.CONFIRM

    return "分析足够深入", Decision.STOP


def human_critical_thinking_critic(
    analyzer_output: str,
    profile: PsychProfile,
) -> tuple[str, Decision]:
    """Critic using human-critical-thinking框架."""
    # 简化版9方向质疑
    concerns = []

    # 检查是否分析了动机层级
    if "动机" not in analyzer_output and "原因" not in analyzer_output:
        concerns.append("未深入分析动机层级")

    # 检查是否有反例/例外考虑
    if "但是" not in analyzer_output and "可能" not in analyzer_output:
        concerns.append("未考虑反例和特殊情况")

    # 检查是否有具体案例支撑
    if "比如" not in analyzer_output and "例如" not in analyzer_output:
        concerns.append("缺少具体案例支撑")

    # 检查极端化表述
    extreme_words = ["总是", "永远", "完全", "绝对"]
    has_extreme = any(w in analyzer_output for w in extreme_words)
    if has_extreme:
        concerns.append("存在极端化表述，需注意")

    if concerns:
        feedback = "9方向质疑反馈：\n" + "\n".join(f"- {i}" for i in concerns)
        return feedback, Decision.CONTINUE

    return "通过质疑检验", Decision.STOP


# === Convenience Functions ===

def create_orchestrator(
    analyzer: Analyzer,
    use_hct: bool = False,
) -> DualAgentOrchestrator:
    """Create orchestrator with specified Critic type."""
    critic_fn = human_critical_thinking_critic if use_hct else default_critic_prompt

    return DualAgentOrchestrator(
        analyzer=analyzer,
        critic_prompt_fn=critic_fn,
    )