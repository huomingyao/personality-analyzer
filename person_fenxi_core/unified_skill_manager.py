"""Unified skill loader for multiple personality analysis frameworks."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Import existing components
from person_fenxi_core.skill_loader import LoadedSkill, SkillLoader


# Known global skills directories
GLOBAL_SKILLS = {
    "liangebodwo-mirror": {
        "name": "liangebodwo-mirror",
        "display": "《了不起的我》五层分析",
        "description": "陈海贤五层分析法：行为层→思维层→关系层→转折层→人生阶段层",
        "triggers": ["分析心理", "心智模式", "转折期", "依恋类型", "五层"],
    },
    "九型人格": {
        "name": "九型人格分析",
        "display": "九型人格 Enneagram",
        "description": "三大中心×九种类型，核心动机/恐惧/欲望分析",
        "triggers": ["九型人格", "Enneagram", "1号", "2号", "3号", "4号", "5号", "6号", "7号", "8号", "9号"],
    },
    "性格色彩分析": {
        "name": "性格色彩分析",
        "display": "FPA 性格色彩",
        "description": "四色动机分析：红蓝黄绿，先天vs后天",
        "triggers": ["红色", "蓝色", "黄色", "绿色", "性格色彩", "FPA"],
    },
    "human-critical-thinking": {
        "name": "human-critical-thinking",
        "display": "HCT 批判思维",
        "description": "9方向质疑：费曼检验+第一性原理+可证伪性+苏格拉底自优化",
        "triggers": ["质疑", "检验", "/hct", "批判"],
    },
}


@dataclass
class PersonalityFramework:
    """Container for a personality analysis framework."""

    skill_id: str
    display_name: str
    description: str
    trigger_keywords: list[str]
    loaded_skill: LoadedSkill | None = None
    prompt_template: str = ""
    system_prompt: str = ""
    enabled: bool = False


class UnifiedSkillManager:
    """Manage multiple personality analysis frameworks."""

    # Base directories for skills - relative to project root
    SKILLS_DIRS = [
        Path(__file__).parent / "skills",
    ]

    def __init__(self) -> None:
        self.loader = SkillLoader()
        self.frameworks: dict[str, PersonalityFramework] = {}
        self._initialize_frameworks()

    def _initialize_frameworks(self) -> None:
        """Initialize framework containers."""
        for key, config in GLOBAL_SKILLS.items():
            self.frameworks[key] = PersonalityFramework(
                skill_id=config["name"],
                display_name=config["display"],
                description=config["description"],
                trigger_keywords=config["triggers"],
            )

    def load_all_available(self) -> dict[str, bool]:
        """Load all skills that exist in the skills directory.

        Returns:
            Dict of skill_id -> success status
        """
        results = {}

        for skill_id, framework in self.frameworks.items():
            loaded = None

            # Try all skill dirs
            for base_dir in self.SKILLS_DIRS:
                if not base_dir.exists():
                    continue

                possible_paths = [
                    base_dir / skill_id,
                    base_dir / framework.display_name,
                    base_dir / self._normalize(framework.display_name),
                ]

                for skill_path in possible_paths:
                    if skill_path.exists():
                        loaded = self.loader.load_skill(skill_path, skill_id)
                        if loaded:
                            break

            if loaded:
                framework.loaded_skill = loaded
                framework.prompt_template = loaded.prompt_template
                framework.system_prompt = self._extract_role(loaded.content)
                framework.enabled = True
                results[skill_id] = True
            else:
                results[skill_id] = False

        return results

    def load_specific(self, skill_id: str) -> bool:
        """Load a specific skill by ID."""
        framework = self.frameworks.get(skill_id)
        if not framework:
            return False

        loaded = None
        for base_dir in self.SKILLS_DIRS:
            if not base_dir.exists():
                continue
            skill_path = base_dir / skill_id
            if skill_path.exists():
                loaded = self.loader.load_skill(skill_path, skill_id)
                break

        if loaded:
            framework.loaded_skill = loaded
            framework.prompt_template = loaded.prompt_template
            framework.system_prompt = self._extract_role(loaded.content)
            framework.enabled = True
            return True

        return False

    def find_available_frameworks(self) -> list[dict[str, Any]]:
        """Find frameworks that have been loaded successfully."""
        available = []

        for fw_id, fw in self.frameworks.items():
            if fw.enabled:
                available.append({
                    "skill_id": fw.skill_id,
                    "display_name": fw.display_name,
                    "description": fw.description,
                    "triggers": fw.trigger_keywords[:3],
                })

        return available

    def _extract_role(self, content: str) -> str:
        """Extract role definition section from SKILL.md content."""
        return self._extract_section(content, "角色定义")

    def _extract_output_template(self, content: str) -> str:
        """Extract the output template from the SKILL.md content.

        Handles the case where the template is inside a markdown code block.
        """
        import re
        # Match ``` or ```markdown code block after "## 输出模板" heading.
        # Allow descriptive text between the heading and the code fence.
        m = re.search(
            r"## 输出模板.*?\n```(?:markdown)?\s*\n(.*?)```",
            content, re.DOTALL
        )
        if m:
            return m.group(1).strip()
        # Fallback: try to get section content (might be short due to ## inside code block)
        section = self._extract_section(content, "输出模板")
        if len(section) > 50:
            return section
        return ""

    def _extract_section(self, content: str, heading: str) -> str:
        """Extract a section by its ## heading from markdown content.

        Supports prefix matching: '分析流程' will match '分析流程（升级版）'.
        """
        import re
        # Try exact match first, then prefix match
        for pattern in [
            rf"## {re.escape(heading)}\s*\n(.*?)(?=\n## )",
            rf"## {re.escape(heading)}[^\n]*\s*\n(.*?)(?=\n## )",
        ]:
            m = re.search(pattern, content, re.DOTALL)
            if m:
                return m.group(1).strip()
        return ""

    def get_system_prompt(self, framework_id: str) -> str:
        """Get the role-based system prompt for a framework."""
        fw = self.frameworks.get(framework_id)
        if fw and fw.system_prompt:
            return fw.system_prompt
        if fw:
            return fw.description
        return "你是一位专业的心理咨询师。"

    def find_framework_by_input(self, user_input: str) -> list[PersonalityFramework]:
        """Find frameworks matching user input."""
        input_lower = user_input.lower()
        matches = []

        for fw in self.frameworks.values():
            if not fw.enabled:
                continue

            for trigger in fw.trigger_keywords:
                if trigger.lower() in input_lower:
                    matches.append(fw)
                    break

        # If no match, default to first available
        if not matches:
            for fw in self.frameworks.values():
                if fw.enabled:
                    matches.append(fw)
                    break

        return matches

    def build_prompt(
        self,
        framework_id: str,
        target: str,
        materials: str,
    ) -> str:
        """Build analysis prompt for a framework.

        Constructs a directive prompt that forces the LLM to execute
        the skill's analysis workflow step by step and produce output
        matching the skill's output template exactly.
        """
        fw = self.frameworks.get(framework_id)
        if not fw or not fw.enabled:
            return self._fallback_prompt(target, materials)

        # Extract the output template and analysis workflow from the skill content
        content = fw.loaded_skill.content if fw.loaded_skill else ""
        template = self._extract_section(content, "输出模板")
        workflow = self._extract_section(content, "分析流程")

        sections = [
            # === PHASE 1: DIRECTIVE (strongest, read first) ===
            f"你现在的任务是：用【{fw.display_name}】框架，对目标人物进行完整心理分析。",
            "",
            "## 你必须严格执行的步骤（每一步都不能跳过）",
            "",
        ]

        if workflow:
            # Rewrite workflow as numbered directives
            sections.append(workflow)
            sections.append("")
        else:
            # Fallback: use the full prompt_template which contains everything
            sections.append(fw.prompt_template[:2000])
            sections.append("")

        sections.extend([
            "## 分析目标",
            f"姓名：{target}",
            "",
            "## 原始材料",
            materials,
            "",
            "---",
            "",
            "## 核心理论知识（需要你内化后使用）",
            fw.prompt_template[:3000],  # theory + behavior lookup, limit length
            "",
            "---",
            "",
        ])

        # === PHASE 2: OUTPUT FORMAT (recency effect — read last, remember best) ===
        template = self._extract_output_template(content)
        if template:
            sections.extend([
                "## 输出格式（必须一字不差地遵循此模板）",
                template,
                "",
            ])
        else:
            sections.extend([
                "请输出完整的结构化分析报告。",
                "",
            ])

        sections.extend([
            "## 最终检查清单",
            "- 是否真正追问了每个行为背后的「为什么」？",
            "- 是否用「不共存铁律」检验了色彩组合？",
            "- 是否区分了先天性格和后天个性？",
            "- 输出是否严格遵循了上面的模板格式？",
        ])

        return "\n".join(sections)

    def build_multi_framework_prompt(
        self,
        target: str,
        materials: str,
        framework_ids: list[str] | None = None,
    ) -> str:
        """Build prompt using multiple frameworks."""
        enabled_frameworks = [
            fw for fw_id, fw in self.frameworks.items()
            if fw.enabled
        ]

        if not framework_ids:
            framework_ids = [fw_id for fw_id, fw in self.frameworks.items() if fw.enabled]

        sections = [
            f"# 综合心理分析：{target}",
            "",
            f"材料：{materials}",
            "",
            "="*50,
        ]

        # 第一步：让LLM分别用各框架分析，得出完整结论
        for i, fw_id in enumerate(framework_ids, 1):
            fw = self.frameworks.get(fw_id)
            if not fw or not fw.enabled:
                continue

            sections.extend([
                f"",
                f"---",
                f"【框架{i}】{fw.display_name}",
                f"",
                fw.description,  # 框架介绍
                f"",
                "---",
                fw.prompt_template,  # 完整prompt，不截断
                f"",
            ])

        # 第二步：让LLM综合所有框架结论，给出总体结论
        sections.extend([
            "="*50,
            "",
            "## 最终综合分析要求",
            "",
            "请依次完成以下任务：",
            "",
            "### 1. 各框架独立结论",
            "上面已经分别给出了各框架的分析结论，请确保每个框架的结论完整、深入。",
            "",
            "### 2. 综合结论",
            "请综合以上所有框架的观点，找出：",
            "- 各框架结论中的共同点和互补之处",
            "- 各框架结论中存在矛盾或冲突的地方",
            "- 形成对分析对象的完整统一画像（包括：行为模式、性格特点、人际关系、优势与风险、发展建议）",
        ])

        return "\n".join(sections)

    def get_framework_info(self, framework_id: str) -> dict[str, Any] | None:
        """Get info for a specific framework."""
        fw = self.frameworks.get(framework_id)
        if not fw:
            return None

        return {
            "skill_id": fw.skill_id,
            "display_name": fw.display_name,
            "description": fw.description,
            "enabled": fw.enabled,
            "triggers": fw.trigger_keywords,
        }

    def _normalize(self, name: str) -> str:
        """Normalize Chinese name for directory."""
        return name.replace(" ", "_").replace("/", "_")

    def _fallback_prompt(self, target: str, materials: str) -> str:
        """Fallback prompt when no framework available."""
        return f"""# 心理分析：{target}

材料：{materials}

请进行心理分析，包括：
- 行为模式
- 思维方式
- 关系特点
- 建议
"""


def create_unified_manager() -> UnifiedSkillManager:
    """Create and initialize unified manager."""
    manager = UnifiedSkillManager()
    manager.load_all_available()
    return manager


def quick_analyze(
    target: str,
    materials: str,
    preferred_framework: str | None = None,
) -> str | None:
    """Quick analysis using available frameworks.

    Args:
        target: Target to analyze
        materials: Materials
        preferred_framework: Optional preferred framework ID

    Returns:
        Built prompt or None if no framework available
    """
    manager = create_unified_manager()

    if preferred_framework:
        return manager.build_prompt(preferred_framework, target, materials)

    available = manager.find_available_frameworks()
    if not available:
        return None

    return manager.build_multi_framework_prompt(target, materials)