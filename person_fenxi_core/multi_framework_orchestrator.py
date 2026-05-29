"""Multi-framework orchestrator for independent parallel analysis.

Uses CriticAgent for cross-framework review and revision.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from person_fenxi_core.critic_agent import (
    CriticAgent,
    CriticReport,
    FrameworkConclusion,
    MultiFrameworkReviewResult,
    CrossFrameworkIssue,
)
from person_fenxi_core.llm_client import MiniMaxClient
from person_fenxi_core.unified_skill_manager import UnifiedSkillManager


@dataclass
class MultiFrameworkResult:
    """Result of multi-framework analysis."""

    conclusions: list[FrameworkConclusion] = field(default_factory=list)
    reviews: list[CriticReport] = field(default_factory=list)
    cross_framework_issues: list[CrossFrameworkIssue] = field(default_factory=list)
    has_contradictions: bool = False
    resolved: bool = False

    def get_independent_reports(self) -> list[dict[str, Any]]:
        """Get formatted independent reports for each framework."""
        reports = []
        for concl in self.conclusions:
            report = {
                "framework_id": concl.framework_id,
                "display_name": concl.display_name,
                "report": concl.conclusion,
                "key_traits": concl.key_traits,
            }
            # Find corresponding review
            for review in self.reviews:
                if review.target == concl.framework_id or review.target == concl.display_name:
                    report["review"] = {
                        "decision": review.decision,
                        "findings_count": len(review.findings),
                    }
                    break
            reports.append(report)
        return reports


class MultiFrameworkOrchestrator:
    """Orchestrate independent multi-framework analysis with Critic review.

    流程：
    1. 并行触发各框架独立分析
    2. 用 CriticAgent 审查每个框架的结论
    3. 用 CriticAgent 检测跨框架矛盾
    4. 用 CriticAgent 生成修订 prompt
    5. 触发对应框架重新审视
    6. 输出各框架独立报告
    """

    def __init__(
        self,
        skill_manager: UnifiedSkillManager | None = None,
        llm_client: MiniMaxClient | None = None,
    ) -> None:
        self.skill_manager = skill_manager or UnifiedSkillManager()
        self.skill_manager.load_all_available()
        self.llm = llm_client or MiniMaxClient()
        self.critic = CriticAgent()  # 使用 CriticAgent 统一处理

    def run_parallel_analysis(
        self,
        target: str,
        materials: str,
        framework_ids: list[str],
        max_iterations: int = 2,
    ) -> MultiFrameworkResult:
        """Run multi-framework analysis with Critic review.

        Args:
            target: Person being analyzed
            materials: Source materials
            framework_ids: List of framework IDs to use
            max_iterations: Max revision iterations

        Returns:
            MultiFrameworkResult with independent reports
        """
        result = MultiFrameworkResult()

        # Step 1: Run initial analysis for each framework
        initial_conclusions = self._run_framework_analysis(target, materials, framework_ids)
        result.conclusions = initial_conclusions

        # Step 2: Use CriticAgent to review all frameworks together (including cross-framework detection)
        review_result = self.critic.review_multiple_frameworks(target, initial_conclusions)

        result.reviews = review_result.individual_reviews
        result.cross_framework_issues = review_result.cross_framework_issues

        # Step 3: If issues found, trigger revision using CriticAgent's revision prompts
        if result.cross_framework_issues and max_iterations > 0:
            result.has_contradictions = True
            result.resolved = self._resolve_issues(
                result, target, materials, review_result.revision_prompts, max_iterations
            )
        else:
            result.resolved = len(result.cross_framework_issues) == 0

        return result

    def _run_framework_analysis(
        self,
        target: str,
        materials: str,
        framework_ids: list[str],
    ) -> list[FrameworkConclusion]:
        """Run analysis for each framework independently."""
        conclusions = []

        for fw_id in framework_ids:
            conclusion = self._analyze_single_framework(target, materials, fw_id)
            if conclusion:
                conclusions.append(conclusion)

        return conclusions

    def _analyze_single_framework(
        self,
        target: str,
        materials: str,
        framework_id: str,
    ) -> FrameworkConclusion | None:
        """Analyze with a single framework."""
        prompt = self.skill_manager.build_prompt(framework_id, target, materials)
        system_prompt = self.skill_manager.get_system_prompt(framework_id)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        try:
            response = self.llm.chat_completion(messages, temperature=0.7, max_tokens=8192, timeout=180.0)
            conclusion_text = response.content
        except Exception as e:
            conclusion_text = f"分析失败: {str(e)}"

        fw_info = self.skill_manager.get_framework_info(framework_id)
        display_name = fw_info.get("display_name", framework_id) if fw_info else framework_id

        key_traits = self._extract_key_traits(conclusion_text)

        return FrameworkConclusion(
            framework_id=framework_id,
            display_name=display_name,
            conclusion=conclusion_text,
            key_traits=key_traits,
        )

    def _resolve_issues(
        self,
        result: MultiFrameworkResult,
        target: str,
        materials: str,
        revision_prompts: dict[str, str],
        max_iterations: int,
    ) -> bool:
        """Resolve issues using CriticAgent's revision prompts."""
        all_resolved = True

        for iteration in range(max_iterations):
            if not result.cross_framework_issues:
                break

            for fw_id, revision_prompt in revision_prompts.items():
                # Get system prompt
                system_prompt = self.skill_manager.get_system_prompt(fw_id)

                # Call LLM with revision prompt
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": revision_prompt},
                ]

                try:
                    response = self.llm.chat_completion(
                        messages, temperature=0.7, max_tokens=4096, timeout=180.0
                    )
                    revised_conclusion = response.content

                    # Update the conclusion
                    self._update_conclusion(result, fw_id, revised_conclusion)
                except Exception:
                    all_resolved = False
                    continue

            # Re-check for remaining issues using CriticAgent
            current_conclusions = result.conclusions
            new_review_result = self.critic.review_multiple_frameworks(target, current_conclusions)

            if not new_review_result.cross_framework_issues:
                result.cross_framework_issues = []
                return True

            result.cross_framework_issues = new_review_result.cross_framework_issues
            # Update revision prompts for next iteration
            revision_prompts = new_review_result.revision_prompts
            all_resolved = False

        return all_resolved

    def _update_conclusion(
        self,
        result: MultiFrameworkResult,
        framework_id: str,
        revised_conclusion: str,
    ) -> None:
        """Update a framework's conclusion with revised version."""
        for i, concl in enumerate(result.conclusions):
            if concl.framework_id == framework_id:
                key_traits = self._extract_key_traits(revised_conclusion)
                result.conclusions[i] = FrameworkConclusion(
                    framework_id=framework_id,
                    display_name=concl.display_name,
                    conclusion=revised_conclusion,
                    key_traits=key_traits,
                )
                break

    def _extract_key_traits(self, conclusion: str) -> list[str]:
        """Extract key traits from conclusion for comparison."""
        import re

        traits = []

        # Extract FPA colors
        colors = re.findall(r"(红色|蓝色|黄色|绿色)", conclusion)
        traits.extend(colors)

        # Extract behavior patterns
        behaviors = re.findall(r"(主动|被动|外向|内向|开放|保守)", conclusion)
        traits.extend(behaviors)

        # Extract Enneagram types
        types = re.findall(r"([1-9])号", conclusion)
        traits.extend([f"{t}号" for t in types])

        return list(set(traits))

    def format_independent_reports(
        self,
        result: MultiFrameworkResult,
    ) -> str:
        """Format result as independent reports (not merged)."""
        sections = []

        for i, concl in enumerate(result.conclusions, 1):
            sections.append(f"""
╔══════════════════════════════════════════════════════════╗
║ 【框架{i}】{concl.display_name}                            ║
╠══════════════════════════════════════════════════════════╣
{concl.conclusion}
╚══════════════════════════════════════════════════════════╝
""")

            # Add review summary if available
            if i - 1 < len(result.reviews):
                review = result.reviews[i - 1]
                if review.findings:
                    sections.append(f"**Critic审查**: 发现 {len(review.findings)} 个问题")
                elif review.decision == "STOP":
                    sections.append("**Critic审查**: 通过")

            sections.append("")

        # Add cross-framework issues summary if any
        if result.cross_framework_issues:
            sections.append("""
## 跨框架矛盾检测结果

以下矛盾已被检测：
""")
            for j, issue in enumerate(result.cross_framework_issues, 1):
                sections.append(f"""
### 矛盾 {j}
- 类型: {issue.type}
- 描述: {issue.description}
- 涉及框架: {", ".join(issue.frameworks)}
- 建议: {issue.suggestion}
""")

        if result.resolved:
            sections.append("\n✅ 所有矛盾已解决")

        return "\n".join(sections)


def create_orchestrator(
    skill_manager: UnifiedSkillManager | None = None,
    llm_client: MiniMaxClient | None = None,
) -> MultiFrameworkOrchestrator:
    """Create and return a multi-framework orchestrator."""
    return MultiFrameworkOrchestrator(skill_manager=skill_manager, llm_client=llm_client)