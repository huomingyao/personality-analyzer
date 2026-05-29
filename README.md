---
name: personality-analyzer
description: |
  多框架人格分析系统。集成性格色彩学、九型人格、《了不起的我》等多个心理学框架，
  使用 AI + 交叉审查机制，提供深度人格画像。
trigger: 分析人格 / 性格分析 / 人格画像 / 心理分析 / 多框架分析
---

<div align="center">

# 🎭 Personality Analyzer

> 多框架人格分析系统 · 穿透行为表象，洞悉深层动机

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)

---

**多框架协同 | AI 驱动 | 交叉审查 | 深度洞察**

| 框架 | 核心理论 | 分析维度 |
|:---:|:---:|:---|
| 🎨 性格色彩 | 乐嘉 FPA 四色动机 | 红·蓝·黄·绿 先天性格 |
| 🧘 九型人格 | 九种核心人格类型 | 翼型·健康层级·动态迁移 |
| 🔍 了不起的我 | 陈海贤心智模式 | 五层心智结构分析 |

</div>

---

## ✨ 核心特性

- **🔄 多框架并行分析**：同时调用多个心理学框架，独立分析后再交叉验证
- **🕵️ 交叉审查机制**：使用 CriticAgent 检测框架间矛盾，确保结论一致性
- **📚 技能库热插拔**：SKILL.md 格式规范，运行时动态加载心理学知识
- **🔍 向量检索增强**：基于语义的心理学知识库，提升分析深度
- **💬 多轮对话分析**：支持渐进式信息收集，模拟心理咨询访谈流程
- **🌐 API + 插件双端**：提供 FastAPI 服务和浏览器插件两种使用方式

---

## 🚀 快速开始

### 安装依赖

```bash
git clone https://github.com/huomingyao/personality-analyzer.git
cd personality-analyzer
pip install -r requirements.txt
```

### 快速分析（Python）

```python
from person_fenxi_core.multi_framework_orchestrator import create_orchestrator

orchestrator = create_orchestrator()

result = orchestrator.run_parallel_analysis(
    target="张三",
    materials="""张三是一名产品经理，最近换了工作。
    他经常主动加班到很晚，但从不抱怨。
    在会议上，他总是第一个发言，提出很多想法。
    但当别人反驳时，他会有点生气...""",
    framework_ids=["性格色彩分析", "九型人格", "liangebodwo-mirror"]
)

print(orchestrator.format_independent_reports(result))
```

### 启动 API 服务

```bash
cd backend/api
uvicorn server:app --reload --port 8000
```

访问 `http://localhost:8000/docs` 查看 API 文档。

---

## 📋 系统架构

```
personality-analyzer/
├── person_fenxi_core/          # 🎯 核心分析引擎
│   ├── analyzer.py            # 多轮对话分析器
│   ├── multi_framework_orchestrator.py  # 多框架编排器
│   ├── unified_skill_manager.py  # 技能管理器
│   ├── skill_loader.py        # 技能加载器
│   ├── critic_agent.py        # 交叉审查 Agent
│   ├── llm_client.py          # LLM 客户端
│   └── skills/                # 📚 内置心理学技能
│       ├── 性格色彩分析/       # FPA 四色分析
│       ├── 九型人格/           # Enneagram 分析
│       ├── liangebodwo-mirror/ # 心智模式分析
│       └── human-critical-thinking/  # 批判性思维
│
├── backend/                   # 🌐 后端服务
│   ├── api/server.py         # FastAPI 服务
│   ├── analyzer/             # 冲突分析引擎
│   └── models/                # 数据模型
│
├── frontend/                  # 🧩 浏览器插件
│   ├── manifest.json         # 插件清单
│   ├── sidepanel/            # 侧边面板 UI
│   └── content_script/       # 注入脚本
│
├── conflict_patterns/         # ⚠️ 冲突模式库
│   └── patterns.yaml          # 冲突规则定义
│
└── tests/                     # 🧪 测试套件
```

---

## 🧠 分析框架详解

### 🎨 性格色彩分析 (FPA)

基于乐嘉《性格色彩学》，分析先天性格与后天个性。

| 色彩 | 核心动机 | 核心问题 |
|:---:|:---:|:---|
| 🔴 红色 | 快乐 | "这样做我开心吗？" |
| 🔵 蓝色 | 完美 | "这样对吗？够好吗？" |
| 🟡 黄色 | 控制 | "谁说了算？我要赢！" |
| 🟢 绿色 | 稳定 | "别变！别找我麻烦！" |

### 🧘 九型人格 (Enneagram)

九种核心人格类型，分析翼型、健康层级和动态迁移。

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

### 🔍 心智模式分析 (《了不起的我》)

五层分析法，洞悉深层心智结构。

| 层次 | 层面 | 核心问题 |
|:---:|:---:|:---|
| 🥇 | 行为层 | TA 想不想改变？什么在阻止TA？ |
| 🥈 | 思维层 | TA 用什么方式看待世界？ |
| 🥉 | 关系层 | TA 在关系中是什么角色？ |
| 4️⃣ | 转折层 | TA 经历过怎样的转变？ |
| 5️⃣ | 人生阶段层 | TA 处于什么人生阶段？ |

---

## 🔄 工作流程

```
┌─────────────────────────────────────────────────────────────────┐
│                        多框架分析流程                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐                                                  │
│  │  输入材料  │  ── 聊天记录/文章/问卷/发言                     │
│  └────┬─────┘                                                  │
│       │                                                         │
│       ▼                                                         │
│  ┌─────────────────────────────────────────┐                    │
│  │     🎯 并行触发多框架独立分析            │                    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐  │                    │
│  │  │性格色彩  │ │九型人格 │ │心智模式 │  │                    │
│  │  └────┬────┘ └────┬────┘ └────┬────┘  │                    │
│  └───────┼──────────┼──────────┼─────────┘                    │
│          │          │          │                                │
│          ▼          ▼          ▼                                │
│  ┌─────────────────────────────────────────┐                    │
│  │     🕵️ CriticAgent 交叉审查             │                    │
│  │  1. 审查每个框架的结论                   │                    │
│  │  2. 检测跨框架矛盾                     │                    │
│  │  3. 生成修订提示                       │                    │
│  └───────┬──────────┬──────────┬─────────┘                    │
│          │          │          │                                │
│          ▼          ▼          ▼                                │
│  ┌─────────────────────────────────────────┐                    │
│  │     📊 输出各框架独立报告                │                    │
│  │  + 矛盾检测结果 + 修订建议              │                    │
│  └─────────────────────────────────────────┘                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📖 使用示例

### 单框架快速分析

```python
from person_fenxi_core.skill_loader import SkillLoader

loader = SkillLoader()
skill = loader.load_skill("性格色彩分析")

result = skill.analyze("他总是第一个到公司，主动帮同事解决问题，\n但当别人做得不够好时会很严厉批评...")

print(result)
# 输出: 🔴 红色为主（快乐导向+社交动力）
#       🟡 黄色次之（控制欲+追求卓越）
```

### 多框架深度分析

```python
from person_fenxi_core.multi_framework_orchestrator import create_orchestrator

orchestrator = create_orchestrator()

# 三框架并行分析
result = orchestrator.run_parallel_analysis(
    target="李四",
    materials="李四的材料...",
    framework_ids=["性格色彩分析", "九型人格", "liangebodwo-mirror"]
)

# 输出独立报告
print(orchestrator.format_independent_reports(result))
```

### API 调用

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "target": "王五",
    "materials": "王五的行为描述...",
    "frameworks": ["性格色彩分析", "九型人格"]
  }'
```

---

## 🛠️ 开发指南

### 添加新框架

1. 在 `person_fenxi_core/skills/` 下创建新目录
2. 编写 `SKILL.md` 定义技能规范
3. 框架自动被 SkillLoader 识别并加载

```markdown
---
name: new_framework
description: 新框架描述
trigger: 触发关键词
---

# 新框架分析指南

[框架理论内容]
```

### 运行测试

```bash
pytest tests/ -v
```

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
| [scamminator](https://github.com/huomingyao/scamminator) | AI 反诈机器人 |

---

## 📄 License

MIT License — 见 [LICENSE](LICENSE) 文件

---

<div align="center">

_Built with 🔥 by [火铭遥](https://github.com/huomingyao)_

_🎭 洞悉人心，超越表象_

</div>
