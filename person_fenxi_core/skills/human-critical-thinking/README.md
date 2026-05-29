# Human Critical Thinking v1.3

> Auto-activates critical thinking pipeline for AI agents. Full-loop: Feynman → First-principles → Falsifiability → Socratic. Token-controlled depth.

## Overview

**Human Critical Thinking** is a hot-pluggable skill that gives any AI agent a structured critical thinking pipeline. It activates automatically at every conversation start and guides the agent through five phases:

| Phase | Purpose | Key Method |
|-------|---------|------------|
| **M1** | Requirement Understanding | 9-angle exploration + Feynman verification |
| **M2** | Problem Analysis | 9-direction analysis + First-principles + Probability |
| **M3** | Execution Planning | 9-dimension planning + Concrete steps |
| **M4** | Task Execution | Dual-branch decision + Falsifiability + MoSCoW |
| **M5** | Self-Optimization | Socratic reflection + Token efficiency + Memory |

## Key Features

- ✅ Only full-loop skill (理解→分析→规划→执行→自优化)
- ✅ Token-controlled depth (low/mid/high: 2050/2580/3000 tokens)
- ✅ Scene detection (skip M2-M3 for simple Q&A)
- ✅ Domain-adaptive templates (coding/business/education)
- ✅ Anti-flood mechanism (first=full, subsequent=light)
- ✅ Cross-session memory (patterns.json with 50-session history)
- ✅ Hot-pluggable: Qclaw/OpenClaw/Hermes/any agent

## Quick Start

Copy `SKILL.md` to your agent's skills directory:

- **Trae**: `.trae/skills/`
- **OpenClaw**: `~/.qclaw/skills/`
- **Hermes**: skills registry path

The skill auto-activates at conversation start. Manual control:
- `/hct` - analyze current topic
- `/hct-full` - force full pipeline (overrides anti-flood)
- `/hct-refresh` - re-analyze same topic
- `/hct-config key=val` - adjust configuration

## Architecture

```
P0 BOOTSTRAP → P1 M1(Understand) → P2 M2(Analyze) → P3 M3(Plan) → P4 M4(Execute) → P5 M5(Optimize)
```

**Core Principle**: 实事求是 (Seek truth from facts). Every question earns its token; every answer evidence-based.

## Version History

- **v1.3** (2026-05-20): Precision fix (9.1→9.9). Scene detection, similarity algorithm, domain templates, progressive disclosure
- **v1.2** (2026-05-20): Competitive optimization (~480t saved, ~17% reduction)
- **v1.1** (2026-05-20): Major enhancement
- **v1.0** (2026-05-19): Initial release

## License

MIT
