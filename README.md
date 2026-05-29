---
name: personality-analyzer
description: |
  多框架人格分析系统。集成性格色彩学、九型人格、心智模式等多个心理学框架，
  使用 AI + 交叉审查机制，提供深度人格画像。
trigger: 分析人格 / 性格分析 / 人格画像 / 心理分析 / 多框架分析
---

<div align="center">

# 🎭 Personality Analyzer

> 多框架人格分析系统 · 穿透行为表象，洞悉深层动机

[![License](https://img.shields.io/badge/License-Personal_Use_Only-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)

---

**多框架协同 | AI 驱动 | 交叉审查 | 深度洞察**

| 框架 | 核心理论 | 分析维度 |
|:---:|:---:|:---|
| 🎨 性格色彩 | 乐嘉 FPA 四色动机 | 红·蓝·黄·绿 先天性格 |
| 🧘 九型人格 | 九种核心人格类型 | 翼型·健康层级·动态迁移 |
| 🔍 心智模式 | 陈海贤《了不起的我》 | 五层心智结构分析 |
| 💡 批判性思维 | 元认知审查 | 论证质量·认知偏误检测 |

</div>

---

## ✨ 核心特性

- **🔄 多框架并行分析**：同时调用多个心理学框架，独立分析后再交叉验证
- **🕵️ 交叉审查机制**：CriticAgent 检测框架间矛盾，确保结论一致性
- **📚 技能库热插拔**：SKILL.md 格式规范，运行时动态加载心理学知识
- **🔍 向量检索增强**：基于语义的心理学知识库，提升分析深度
- **💬 多轮对话分析**：渐进式信息收集，模拟心理咨询访谈流程
- **⚡ 语料转技能**：输入文档自动构建分析知识库

---

## 🚀 快速开始

```bash
# 克隆仓库
git clone https://github.com/huomingyao/personality-analyzer.git
cd personality-analyzer
pip install -r requirements.txt
```

### 单框架分析

```python
from person_fenxi_core.skill_loader import SkillLoader

loader = SkillLoader()
skill = loader.load_skill("性格色彩分析")

result = skill.analyze(
    "他总是第一个到公司，主动帮同事解决问题，"
    "但当别人做得不够好时会很严厉批评..."
)
```

### 多框架并行分析

```python
from person_fenxi_core.multi_framework_orchestrator import create_orchestrator

orchestrator = create_orchestrator()

result = orchestrator.run_parallel_analysis(
    target="张三",
    materials="""张三是一名产品经理，最近换了工作。
    他经常主动加班到很晚，但从不抱怨。
    在会议上，他总是第一个发言，提出很多想法...""",
    framework_ids=["性格色彩分析", "九型人格", "liangebodwo-mirror"]
)

# 输出各框架独立报告 + 交叉审查结果
print(orchestrator.format_independent_reports(result))
```

---

## 📋 项目结构

```
personality-analyzer/
├── person_fenxi_core/          # 🎯 核心分析引擎
│   ├── analyzer.py                 # 多轮对话分析器
│   ├── multi_framework_orchestrator.py  # 多框架编排
│   ├── unified_skill_manager.py    # 技能管理器
│   ├── skill_loader.py             # 技能加载器
│   ├── critic_agent.py             # 交叉审查 Agent
│   ├── llm_client.py               # LLM 客户端
│   ├── config.py                   # 全局配置
│   ├── router.py                   # 分析路由
│   ├── session.py                  # 会话管理
│   ├── corpus2skill/               # 语料→技能转换
│   ├── storage/                    # 向量存储
│   └── skills/                     # 📚 内置心理学技能
│       ├── 性格色彩分析/            # FPA 四色分析
│       ├── 九型人格/                # Enneagram 分析
│       ├── liangebodwo-mirror/      # 心智模式分析
│       └── human-critical-thinking/ # 批判性思维审查
│
├── README.md
└── LICENSE
```

---

## 🧠 分析框架详解

### 🎨 性格色彩分析 (FPA)

基于乐嘉《性格色彩学》，穿透行为表象，分析先天性格与后天个性。

| 色彩 | 核心动机 | 核心问题 |
|:---:|:---:|:---|
| 🔴 红色 | 快乐 | "这样做我开心吗？" |
| 🔵 蓝色 | 完美 | "这样对吗？够好吗？" |
| 🟡 黄色 | 控制 | "谁说了算？我要赢！" |
| 🟢 绿色 | 稳定 | "别变！别找我麻烦！" |

**核心方法论：行为 → 动机追问 → 色彩判定 → 先天/后天分离**

### 🧘 九型人格 (Enneagram)

九种核心人格类型，分析翼型、健康层级和动态迁移线。

```
      8        9        1
     /│\      /│\      /│\
    8 │ 1    9 │ 1    8 │ 9
      │        │        │
  7───┼───3  8───┼───2  7───┼───2
      │        │        │
     6 │ 2    7 │ 3    6 │ 3
      \│/      \│/      \│/
      5        4        4
```

### 🔍 心智模式分析

基于陈海贤《了不起的我》五层分析法：

| 层次 | 层面 | 核心问题 |
|:---:|:---:|:---|
| 🥇 | 行为层 | TA 想不想改变？什么在阻止TA？ |
| 🥈 | 思维层 | TA 用什么方式看待世界？ |
| 🥉 | 关系层 | TA 在关系中是什么角色？ |
| 4️⃣ | 转折层 | TA 经历过怎样的转变？ |
| 5️⃣ | 人生阶段 | TA 处于什么人生阶段？ |

---

## 🔄 多框架分析流程

```
  输入材料（聊天记录/文章/问卷/发言）
         │
         ▼
  ┌──────────────────────────┐
  │   🎯 并行触发多框架分析   │
  │  ┌───────┐ ┌───────┐    │
  │  │色彩分析│ │九型   │ ...│
  │  └───┬───┘ └───┬───┘    │
  └──────┼──────────┼────────┘
         │          │
         ▼          ▼
  ┌──────────────────────────┐
  │  🕵️ CriticAgent 交叉审查 │
  │  · 审查各框架结论         │
  │  · 检测跨框架矛盾         │
  │  · 生成修订提示           │
  └────────────┬─────────────┘
               │
               ▼
  ┌──────────────────────────┐
  │  📊 输出各框架独立报告    │
  │  + 矛盾检测 + 修订建议    │
  └──────────────────────────┘
```

---

## 🛠️ 扩展开发

### 添加新的分析框架

在 `person_fenxi_core/skills/` 下创建新目录，编写 `SKILL.md`：

```markdown
---
name: new_framework
description: 新框架描述
trigger: 触发关键词
---

# 新框架分析指南

[框架理论内容与分析步骤]
```

框架会被 SkillLoader 自动识别并加载。

---

## 📚 参考资料

| 框架 | 来源 |
|------|------|
| 性格色彩学 | 乐嘉《FPA性格色彩》 |
| 九型人格 | 海伦·帕尔默《九型人格》 |
| 心智模式 | 陈海贤《了不起的我》 |

---

## 🔗 相关项目

| 项目 | 描述 |
|------|------|
| [liangebodwo-mirror](https://github.com/huomingyao/liangebodwo-mirror) | 心智模式五层分析 |
| [color_human](https://github.com/huomingyao/color_human) | 性格色彩分析 |

---

## 📄 License

Copyright (c) 2024 火铭遥 — 保留所有权利。

本软件仅供个人学习、研究使用，禁止商用和二次修改。
详见 [LICENSE](LICENSE) 文件。

---

<div align="center">

_Built with 🔥 by [火铭遥](https://github.com/huomingyao)_

_🎭 洞悉人心，超越表象_

</div>
