"""完整版Critic Agent - 9方向+证伪+索卡尔反思 + 跨框架检测"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class CriticDimension(Enum):
    """Critic的9个质疑维度."""

    EVIDENCE_SUFFICIENCY = "evidence_sufficientity"  # 1. 证据充分性
    LOGICAL_CONSISTENCY = "logical_consistency"  # 2. 逻辑一致性
    MOTIVATION_REASONABLENESS = "motivation_reasonableness"  # 3. 动机合理性
    SITUATIONAL_DEPENDENCE = "situational_dependence"  # 4. 情境依赖性
    EXTREMIZATION_TENDENCY = "extremization_tendency"  # 5. 极端化倾向
    COUNTEREXAMPLE_CONSIDERATION = "counterexample_consideration" # 6. 反例考虑
    MOTIVATION_HIERARCHY = "motivation_hierarchy"  # 7. 动机层级
    CHANGE_POSSIBILITY = "change_possibility"  # 8. 变化可能
    BLIND_SPOT_IDENTIFICATION = "blind_spot_identification"  # 9. 盲点识别


class FalsificationType(Enum):
    """证伪的类型."""

    DIRECT_COUNTER = "direct_counter"  # 直接反例
    ALTERNATIVE_EXPLANATION = "alternative_explanation"  # 替代解释
    BOUNDARY_CASE = "boundary_case"  # 边界情况
    TEMPORAL_INCONSISTENCY = "temporal_inconsistency"  # 时间不一致


class SocraticProbe(Enum):
    """索卡尔式追问."""

    WHAT_EVIDENCE = "你能提供支持这个结论的具体例子吗？"
    WHAT_IF_NOT = "如果不是这样的话，会是什么情况？"
    ALWAYS_SO = "是否总是这样？有例外吗？"
    WHY_THIS = "为什么是这个原因而不是其他？"
    ANY_ALTERNATIVE = "还有其他可能的解释吗？"
    WHICH_CONTEXT = "在什么情境下这个结论可能不成立？"
    HOW_KNOW = "你怎么知道这是真的？证据在哪？"
    SO_WHAT = "即使成立然后呢？这意味着什么？"


@dataclass
class CriticFinding:
    """Critic的单个发现."""

    dimension: str
    severity: str  # "critical" / "warning" / "info"
    description: str
    question: str  # 索卡尔追问
    suggestion: str


@dataclass
class CriticReport:
    """完整的Critic审查报告."""

    target: str
    findings: list[CriticFinding] = field(default_factory=list)
    decision: str = "CONTINUE"  # CONTINUE / STOP / CONFIRM
    reasoning: str = ""
    strengths: list[str] = field(default_factory=list)
    weaknesses: list[str] = field(default_factory=list)


@dataclass
class FrameworkConclusion:
    """单个框架的分析结论（用于跨框架审查）."""

    framework_id: str
    display_name: str
    conclusion: str  # 完整分析报告
    key_traits: list[str] = field(default_factory=list)


@dataclass
class CrossFrameworkIssue:
    """跨框架检测到的问题."""

    type: str  # "behavior" | "trait" | "motivation"
    frameworks: list[str]  # 涉及的框架
    description: str
    resolve_needed_from: str  # 需要重新审视的框架
    suggestion: str


@dataclass
class MultiFrameworkReviewResult:
    """多框架审查结果."""

    individual_reviews: list[CriticReport]  # 各框架的单独审查报告
    cross_framework_issues: list[CrossFrameworkIssue]  # 跨框架问题
    revision_prompts: dict[str, str]  # framework_id -> 修订prompt


class CriticAgent:
    """完整版Critic Agent

    实现完整的9方向质疑 + 证伪 + 索卡尔反思
    支持单框架审查和多框架跨框架检测
    """

    VERSION = "1.1.0"
    DESCRIPTION = "基于human-critical-thinking框架的完整批评 Agent"

    # 9方向的详细检查列表
    DIMENSION_CHECKLIST = {
        CriticDimension.EVIDENCE_SUFFICIENCY: {
            "name": "证据充分性",
            "question": "有哪些具体证据支持这个结论？",
            "criteria": [
                "是否有具体案例/事件支撑？",
                "证据来源是否可靠？",
                "证据是否足以推出结论？",
            ],
        },
        CriticDimension.LOGICAL_CONSISTENCY: {
            "name": "逻辑一致性",
            "question": "各部分分析逻辑是否自洽？",
            "criteria": [
                "前提和结论是否一致？",
                "各层分析是否矛盾？",
                "是否有逻辑跳跃？",
            ],
        },
        CriticDimension.MOTIVATION_REASONABLENESS: {
            "name": "动机合理性",
            "question": "推断的动机是否合理？",
            "criteria": [
                "是否以己度人？",
                "是否有其他更合理的动机解释？",
                "是否考虑了潜意识动机？",
            ],
        },
        CriticDimension.SITUATIONAL_DEPENDENCE: {
            "name": "情境依赖性",
            "question": "是否考虑了情境因素？",
            "criteria": [
                "是否因人而异？",
                "是否因时因地？",
                "是否忽略了环境因素？",
            ],
        },
        CriticDimension.EXTREMIZATION_TENDENCY: {
            "name": "极端化倾向",
            "question": "是否有过度概括？",
            "criteria": [
                "是否使用绝对词（总是/永远/完全）？",
                "是否忽视了个体差异？",
                "是否以偏概全？",
            ],
        },
        CriticDimension.COUNTEREXAMPLE_CONSIDERATION: {
            "name": "反例考虑",
            "question": "是否考虑了例外情况？",
            "criteria": [
                "有没有反例？",
                "是否过于简单化？",
                "能否举出反例？",
            ],
        },
        CriticDimension.MOTIVATION_HIERARCHY: {
            "name": "动机层级",
            "question": "是否区分了不同动机层级？",
            "criteria": [
                "是否区分表层/深层动机？",
                "是否区分主动/被动？",
                "是否区分想要/应该要？",
            ],
        },
        CriticDimension.CHANGE_POSSIBILITY: {
            "name": "变化可能",
            "question": "是否考虑了改变的可能性？",
            "criteria": [
                "是否认为不可改变？",
                "是否忽视了成长可能？",
                "是否考虑情境变化？",
            ],
        },
        CriticDimension.BLIND_SPOT_IDENTIFICATION: {
            "name": "盲点识别",
            "question": "是否有遗漏的重要维度？",
            "criteria": [
                "是否忽视了重要因素？",
                "是否有未触及的话题？",
                "是否有偏见？",
            ],
        },
    }

    def __init__(self) -> None:
        self.name = "Critic"
        self.version = self.VERSION

    # === 单框架审查（原有功能）===

    def review(
        self,
        target: str,
        analyzer_output: str,
        context: dict[str, Any] | None = None,
    ) -> CriticReport:
        """对Analyzer的输出进行全面审查

        Args:
            target: 被分析的对象
            analyzer_output: Analyzer的完整输出
            context: 可选的上下文

        Returns:
            CriticReport 包含完整审查结果
        """
        report = CriticReport(target=target)

        # 9方向全面审查
        for dimension, config in self.DIMENSION_CHECKLIST.items():
            finding = self._check_dimension(dimension, config, analyzer_output)
            if finding:
                report.findings.append(finding)

        # 进行证伪尝试
        falsifications = self._attempt_falsification(analyzer_output, context)
        for f in falsifications:
            report.findings.append(CriticFinding(
                dimension="falsification",
                severity="warning",
                description=f["comment"],
                question="你能解释这个看似矛盾的现象吗？",
                suggestion=f["suggestion"],
            ))

        # 提取优点和弱点
        self._analyze_strengths_weaknesses(analyzer_output, report)

        # 做出决策
        self._make_decision(report)

        return report

    def _check_dimension(
        self,
        dimension: CriticDimension,
        config: dict,
        analyzer_output: str,
    ) -> CriticFinding | None:
        """检查单个维度"""
        severity = "info"
        description = ""
        suggestion = ""

        output_lower = analyzer_output.lower()

        # 检查各维度的具体指标
        if dimension == CriticDimension.EVIDENCE_SUFFICIENCY:
            has_examples = any(w in output_lower for w in ["例如", "比如", "案例", "具体"])
            if not has_examples:
                severity = "warning"
                description = "缺乏具体案例支撑"
                suggestion = "建议添加至少2个具体案例"

        elif dimension == CriticDimension.EXTREMIZATION_TENDENCY:
            extreme_words = ["总是", "永远", "完全", "绝对", "从不", "一定"]
            has_extreme = any(w in output_lower for w in extreme_words)
            if has_extreme:
                severity = "critical"
                description = "存在极端化表述"
                suggestion = "避免使用绝对词，添加例外说明"

        elif dimension == CriticDimension.COUNTEREXAMPLE_CONSIDERATION:
            has_ambiguity = any(w in output_lower for w in ["但是", "可能", "或许", "不过"])
            if not has_ambiguity:
                severity = "warning"
                description = "未考虑反例和例外"
                suggestion = "添加但是/可能的说明"

        elif dimension == CriticDimension.MOTIVATION_HIERARCHY:
            has_motivation_deep = any(w in output_lower for w in ["潜意识", "深层", "根本原因", "原生家庭"])
            has_motivation_surface = any(w in output_lower for w in ["表面", "直接原因"])
            if not (has_motivation_deep or has_motivation_surface):
                severity = "warning"
                description = "未区分动机层级"
                suggestion = "区分表层动机和深层动机"

        elif dimension == CriticDimension.LOGICAL_CONSISTENCY:
            contradictions = ["一方面...另一方面...", "既...又..."]
            if any(c in output_lower for c in contradictions):
                severity = "warning"
                description = "可能存在逻辑矛盾"

        elif dimension == CriticDimension.CHANGE_POSSIBILITY:
            has_change = any(w in output_lower for w in ["可以改变", "有可能", "会成长", "会变化"])
            if not has_change:
                severity = "warning"
                description = "未考虑改变的可能性"
                suggestion = "添加成长/改变的可能"

        elif dimension == CriticDimension.BLIND_SPOT_IDENTIFICATION:
            blind_spots = ["经济", "身体", "外貌", "健康", "工作", "事业"]
            touched = [bs for bs in blind_spots if bs in output_lower]
            if len(touched) < 2:
                severity = "info"
                description = "可能存在的盲点: 某些生活维度未涉及"
                suggestion = f"可考虑分析: {[bs for bs in blind_spots if bs not in touched][:3]}"

        if severity != "info" or description:
            import random
            question = random.choice(list(SocraticProbe)).value

            return CriticFinding(
                dimension=dimension.value,
                severity=severity,
                description=description,
                question=question,
                suggestion=suggestion,
            )

        return None

    def _attempt_falsification(
        self,
        analyzer_output: str,
        context: dict[str, Any] | None,
    ) -> list[dict]:
        """尝试证伪 - 寻找反例"""
        falsifications = []

        opposite_checks = [
            ("外向", "内向"),
            ("主动", "被动"),
            ("乐观", "悲观"),
            ("开放", "保守"),
        ]

        output_lower = analyzer_output.lower()

        for pos, neg in opposite_checks:
            if pos in output_lower and neg not in output_lower:
                falsifications.append({
                    "type": FalsificationType.DIRECT_COUNTER.value,
                    "comment": f"提到{pos}但未讨论{neg}情况",
                    "suggestion": f"考虑{neg}的可能性",
                })

        return falsifications

    def _analyze_strengths_weaknesses(
        self,
        analyzer_output: str,
        report: CriticReport,
    ) -> None:
        """分析输出的优点和弱点"""
        output_lower = analyzer_output.lower()

        if "可能" in output_lower or "或许" in output_lower:
            report.strengths.append("谨慎使用模糊语气")
        if "但是" in output_lower:
            report.strengths.append("考虑了多角度")
        if any(w in output_lower for w in ["比如", "例如", "如"]):
            report.strengths.append("有具体案例")
        if len(analyzer_output) > 500:
            report.strengths.append("分析较为详细")

        extreme_count = sum(1 for w in ["总是", "永远", "绝对"] if w in output_lower)
        if extreme_count > 2:
            report.weaknesses.append("过度使用绝对词")
        if "所以" in output_lower and "因为" not in output_lower:
            report.weaknesses.append("存在逻辑跳跃")
        if len(analyzer_output) < 100:
            report.weaknesses.append("分析过于简略")

    def _make_decision(self, report: CriticReport) -> None:
        """基于审查结果做出决策"""
        critical_count = sum(1 for f in report.findings if f.severity == "critical")
        warning_count = sum(1 for f in report.findings if f.severity == "warning")

        if critical_count >= 2:
            report.decision = "CONTINUE"
            report.reasoning = f"发现{critical_count}个严重问题，需要继续"
        elif warning_count >= 3:
            report.decision = "CONTINUE"
            report.reasoning = f"发现{warning_count}个警告，需要改进"
        elif len(report.strengths) >= 3 and len(report.weaknesses) <= 1:
            report.decision = "CONFIRM"
            report.reasoning = "优点明显多于弱点，建议确认"
        elif critical_count == 0 and warning_count <= 1:
            report.decision = "STOP"
            report.reasoning = "通过审查，分析足够深入"
        else:
            report.decision = "CONTINUE"
            report.reasoning = "存在一些需要改进的问题"

    def generate_feedback_prompt(self, report: CriticReport) -> str:
        """生成反馈prompt给用户"""
        lines = [
            f"# Critic 审查报告：{report.target}",
            "",
            "## 审查结论",
            f"**{report.decision}** - {report.reasoning}",
            "",
        ]

        if report.findings:
            lines.extend(["## 发现的问题", ""])
            for i, f in enumerate(report.findings, 1):
                lines.append(f"### {i}. [{f.severity.upper()}] {f.dimension}")
                lines.append(f"- 问题: {f.description}")
                lines.append(f"- 追问: {f.question}")
                lines.append(f"- 建议: {f.suggestion}")
                lines.append("")

        if report.strengths:
            lines.extend(["## 优点", *[f"- {s}" for s in report.strengths], ""])

        if report.weaknesses:
            lines.extend(["## 需要改进", *[f"- {w}" for w in report.weaknesses], ""])

        return "\n".join(lines)

    # === 跨框架审查（新增功能）===

    def review_multiple_frameworks(
        self,
        target: str,
        conclusions: list[FrameworkConclusion],
    ) -> MultiFrameworkReviewResult:
        """审查多个框架的结论，检测跨框架矛盾

        Args:
            target: 被分析的对象
            conclusions: 多个框架的分析结论列表

        Returns:
            MultiFrameworkReviewResult 包含单独审查和跨框架问题
        """
        result = MultiFrameworkReviewResult(
            individual_reviews=[],
            cross_framework_issues=[],
            revision_prompts={},
        )

        # Step 1: 对每个框架进行单独审查
        for concl in conclusions:
            review = self.review(target, concl.conclusion, {"framework": concl.framework_id})
            result.individual_reviews.append(review)

        # Step 2: 检测跨框架矛盾
        issues = self._detect_cross_framework_issues(conclusions)
        result.cross_framework_issues = issues

        # Step 3: 为需要修订的框架生成修订 prompt
        for issue in issues:
            fw_id = issue.resolve_needed_from
            if fw_id not in result.revision_prompts:
                concl = next((c for c in conclusions if c.framework_id == fw_id), None)
                if concl:
                    result.revision_prompts[fw_id] = self._build_cross_framework_revision_prompt(
                        target=target,
                        framework_id=fw_id,
                        display_name=concl.display_name,
                        original_conclusion=concl.conclusion,
                        issue=issue,
                        other_conclusions=[c for c in conclusions if c.framework_id != fw_id],
                    )

        return result

    def _detect_cross_framework_issues(
        self,
        conclusions: list[FrameworkConclusion],
    ) -> list[CrossFrameworkIssue]:
        """检测跨框架矛盾"""
        issues = []

        for i in range(len(conclusions)):
            for j in range(i + 1, len(conclusions)):
                concl_a = conclusions[i]
                concl_b = conclusions[j]

                # 检测特质矛盾
                for trait_a in concl_a.key_traits:
                    for trait_b in concl_b.key_traits:
                        if self._is_contradictory_trait(trait_a, trait_b):
                            issues.append(CrossFrameworkIssue(
                                type="trait",
                                frameworks=[concl_a.framework_id, concl_b.framework_id],
                                description=f"特质矛盾: {trait_a} vs {trait_b}",
                                resolve_needed_from=concl_a.framework_id,
                                suggestion=self._get_trait_contradiction_suggestion(trait_a, trait_b),
                            ))

                # 检测行为描述矛盾
                conclusion_a_lower = concl_a.conclusion.lower()
                conclusion_b_lower = concl_b.conclusion.lower()

                behavior_pairs = [
                    ("主动", "被动"),
                    ("外向", "内向"),
                    ("开放", "封闭"),
                ]

                for pos, neg in behavior_pairs:
                    has_pos_a = pos in conclusion_a_lower
                    has_neg_a = neg in conclusion_a_lower
                    has_pos_b = pos in conclusion_b_lower
                    has_neg_b = neg in conclusion_b_lower

                    if (has_pos_a and has_neg_b) or (has_neg_a and has_pos_b):
                        resolve_from = concl_a.framework_id if has_pos_a else concl_b.framework_id
                        issues.append(CrossFrameworkIssue(
                            type="behavior",
                            frameworks=[concl_a.framework_id, concl_b.framework_id],
                            description=f"行为矛盾: {pos} vs {neg}",
                            resolve_needed_from=resolve_from,
                            suggestion=self._get_behavior_contradiction_suggestion(pos, neg),
                        ))

        return issues

    def _is_contradictory_trait(self, trait_a: str, trait_b: str) -> bool:
        """检查两个特质是否矛盾"""
        contradictions = [
            ("内向", "外向"),
            ("被动", "主动"),
            ("开放", "保守"),
            ("红色", "蓝色"),
            ("黄色", "绿色"),
        ]

        for a, b in contradictions:
            if (a in trait_a and b in trait_b) or (b in trait_a and a in trait_b):
                return True

        return False

    def _get_trait_contradiction_suggestion(self, trait_a: str, trait_b: str) -> str:
        """获取特质矛盾的解决建议"""
        if "红色" in trait_a and "蓝色" in trait_b:
            return "红蓝不共存。请检查：哪个是先天核心动机，哪个是后天修饰性行为？"
        if "黄色" in trait_a and "绿色" in trait_b:
            return "黄绿不共存。请检查：追求控制是真实需求还是对不确定性的防御？"
        return f"特质 '{trait_a}' 和 '{trait_b}' 存在矛盾。请重新审视材料，给出更精确的描述。"

    def _get_behavior_contradiction_suggestion(self, pos: str, neg: str) -> str:
        """获取行为矛盾的解决建议"""
        return (
            f"请重新审视材料中关于'{pos}'和'{neg}'的描述。\n"
            f"区分：\n"
            f"- 在哪些场景下表现为{pos}？\n"
            f"- 在哪些场景下表现为{neg}？\n"
            f"- 不同场景下的动机是否一致？\n"
            f"可能情况：同一特质在安全环境下表现为{pos}，在压力下表现为{neg}。"
        )

    def _build_cross_framework_revision_prompt(
        self,
        target: str,
        framework_id: str,
        display_name: str,
        original_conclusion: str,
        issue: CrossFrameworkIssue,
        other_conclusions: list[FrameworkConclusion],
    ) -> str:
        """构建跨框架修订 prompt"""
        other_summary = "\n".join([
            f"- **{c.display_name}**: {c.conclusion[:200]}..."
            for c in other_conclusions
        ])

        return f"""# 【Critic 跨框架审查反馈】

## 分析对象
{target}

## 当前框架
{display_name}

## 你的原始结论
{original_conclusion}

## 其他框架的结论（与之存在矛盾）
{other_summary}

---

## 检测到的问题
**问题类型**: {issue.type}
**描述**: {issue.description}
**建议**: {issue.suggestion}

---

## 需要你重新审视

请基于上述跨框架反馈，重新审视你的分析结论：

1. 材料中哪些证据支持你原来的判断？
2. 是否有其他解释可以兼容两个框架的结论？
3. 能否给出更精确的描述来化解这个矛盾？

请输出优化后的完整分析报告，确保：
- 描述精确、逻辑自洽
- 与其他框架的结论不冲突
- 有充分的证据支撑
"""


# === 便捷函数 ===

def create_critic_agent() -> CriticAgent:
    """创建Critic Agent实例"""
    return CriticAgent()


def review_analysis(
    target: str,
    analyzer_output: str,
    context: dict[str, Any] | None = None,
) -> CriticReport:
    """便捷函数：对分析结果进行审查（单框架）"""
    critic = CriticAgent()
    return critic.review(target, analyzer_output, context)


def review_frameworks(
    target: str,
    conclusions: list[FrameworkConclusion],
) -> MultiFrameworkReviewResult:
    """便捷函数：审查多个框架结论（跨框架）"""
    critic = CriticAgent()
    return critic.review_multiple_frameworks(target, conclusions)