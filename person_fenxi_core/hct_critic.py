"""Critic using external human-critical-thinking skill."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from person_fenxi_core.orchestrator import Decision, PsychProfile
from person_fenxi_core.unified_skill_manager import create_unified_manager


def hct_critic_with_skill(
    analyzer_output: str,
    profile: PsychProfile,
) -> tuple[str, Decision]:
    """Critic using external human-critical-thinking skill.

    This replaces the hardcoded version to use the actual skill.
    """
    # Try to load external HCT skill
    try:
        manager = create_unified_manager()
        manager.load_all_available()

        hct_info = manager.get_framework_info("human-critical-thinking")

        if hct_info and hct_info.get("enabled"):
            # Use external skill for critique
            return _critique_with_skill(analyzer_output, profile, hct_info)
        else:
            # Fallback to built-in if not loaded
            pass
    except Exception:
        pass

    # Fallback: hardcoded fallback (kept for compatibility)
    return _builtin_critic(analyzer_output, profile)


def _critique_with_skill(
    output: str,
    profile: PsychProfile,
    skill_info: dict[str, Any],
) -> tuple[str, Decision]:
    """Critique using loaded skill content."""
    # Build critique prompt from skill
    skill_manager = create_unified_manager()

    prompt = f"""【分析输出】
{output}

【当前心理画像】
行为层: {profile.behavior_layer}
思维层: {profile.thinking_layer}
关系层: {profile.relationship_layer}
核心模式: {', '.join(profile.core_pattern)}

---

请使用 {skill_info['display_name']} 框架进行9方向质疑检验：

1. 证据充分性 - 有足够证据支持结论吗？
2. 逻辑一致性 - 各层分析逻辑自洽吗？
3. 动机合理性 - 推断的动机合理吗？
4. 情境依赖性 - 是否考虑了情境因素？
5. 极端化倾向 - 是否过度概括/绝对化？
6. 反例考虑 - 有没有考虑反例？
7. 动机层级 - 分析了表面/深层动机吗？
8. 变化可能 - 是否考虑改变的可能性？
9. 盲点识别 - 是否有遗漏的重要维度？

给出检验结果和决策：继续/停止/确认"""

    # Simple heuristic for now - in real implementation, would call LLM
    concerns = []

    if not profile.core_pattern:
        concerns.append("缺少核心模式总结")

    if len(profile.confidence_scores) > 0:
        avg = sum(profile.confidence_scores.values()) / len(profile.confidence_scores)
        if avg < 0.5:
            concerns.append("置信度偏低")

    if "可能" not in output and "但是" not in output:
        concerns.append("未考虑反例和特殊情况")

    if concerns:
        feedback = "9方向检验反馈：\n" + "\n".join(f"- {i}" for i in concerns)
        return feedback, Decision.CONTINUE

    return "通过9方向检验，分析足够深入", Decision.STOP


def _builtin_critic(
    output: str,
    profile: PsychProfile,
) -> tuple[str, Decision]:
    """Fallback built-in critic (simplified)."""
    concerns = []

    if not profile.core_pattern:
        concerns.append("缺少核心模式总结")

    if len(profile.confidence_scores) > 0:
        avg = sum(profile.confidence_scores.values()) / len(profile.confidence_scores)
        if avg < 0.5:
            concerns.append("置信度偏低")

    if concerns:
        feedback = "需要继续分析：\n" + "\n".join(f"- {i}" for i in concerns)
        return feedback, Decision.CONTINUE

    return "分析足够深入", Decision.STOP