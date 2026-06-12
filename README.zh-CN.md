[English](README.md) | **中文**

# Agentic Skills 最佳实践

构建 Agent Skills 的最佳实践、示例和培训材料。Agent Skills 是由指令、脚本和资源组成的文件夹，AI 代理可以动态加载这些内容以提升在专业任务上的表现。

**一次编写，随处运行。** 本仓库所有 Skills 均遵循开放的 [Agent Skills 规范](https://agentskills.io/specification)，只使用标准字段、不依赖任何平台私有扩展。同一个 Skill 文件夹无需修改即可在任何实现该规范的平台上使用：Kiro（IDE 和 CLI）、Claude Code、Claude.ai、Claude API 以及其他兼容代理。本仓库的 Skills 已在 Kiro 和 Claude Code 上完成端到端验证（见 [TESTING.md](TESTING.md)）。

本仓库面向 **AWS SA 和开发者**，以 [Kiro](https://kiro.dev) 为主要学习环境，但不会造成任何平台锁定——纯指令型 Skills 完全可移植；少数捆绑可执行 `scripts/` 的 Skills 额外要求目标平台允许执行代码并安装其声明的依赖。

## 快速入门

**新手？** 请按照 [Kiro Skills 快速入门指南](QUICKSTART.md) 在 5 分钟内从零开始创建一个可用的 Skill。

一步将本仓库的 Skills 安装到 Kiro：

```bash
./install.sh hello-world api-design git-workflow   # 或 ./install.sh --all
```

## 仓库内容

- **示例 Skills**: `skills/skills/` 中的生产级示例（创意、技术、企业）
- **Hello World**: `skills/skills/hello-world/` 中的最小可用 Skill，用于验证你的环境配置
- **Skills 工坊**: `skills-workshop/` 中的 6 小时实操培训
- **Skill 模板**: `skills/template/` 中的新 Skill 起始模板
- **软件工程 Skills**: 8 个实用的软件工程工作流 Skills，包括代码审查、Git 工作流、API 设计、Docker Compose 生成、数据库 Schema 设计、CI/CD 流水线、Terraform 模块和 Python 项目初始化
- **安全 SDLC Skills**: 5 个 Scrum + DevSecOps 角色 Skills（威胁建模、安全/用户故事编写、含安全债务的 Sprint 规划、Sprint 安全评审）
- **金融合规**: 将代码/架构变更映射到 PCI-DSS v4.0 和 MAS TRM 控制点的合规检查 Skill，采用按领域组织的参考文件
- **云架构**: AWS Well-Architected 评审 Skill，按支柱组织参考文件（安全、可靠性、成本、性能、运维、可持续性）
- **AI 落地 Skills**: code-standards-adopter（让 AI 生成的代码匹配团队风格）和 legacy-code-testing（重构前的特征测试）
- **Skills 目录**: 完整的分类目录请参见 [skills/CATALOG.md](skills/CATALOG.md)

> **在找文档类 Skills（docx、pdf、pptx、xlsx）？** 它们是 Anthropic 的 source-available（非开源）生产级 Skills。为保持本仓库内容全部使用开源许可，已将其移除——请到官方 [anthropics/skills](https://github.com/anthropics/skills) 仓库获取。

## 仓库结构

```
.
├── QUICKSTART.md              # 5-minute quickstart guide
├── skills/                    # Skills collection (from Anthropic)
│   ├── skills/               # Individual skill folders
│   │   ├── hello-world/      # Minimal example (start here)
│   │   ├── skill-creator/    # Build skills with AI assistance
│   │   ├── frontend-design/  # Example: creative skill
│   │   ├── mcp-builder/      # Example: MCP integration
│   │   ├── api-design/       # Example: engineering workflow skill
│   │   └── ...
│   ├── template/             # Blank skill template
│   └── README.md             # Skills collection docs
├── skills-workshop/           # Workshop training materials
│   ├── 01-fundamentals/      # Progressive disclosure, YAML, structure
│   ├── 02-planning-design/   # Use cases, descriptions, triggers
│   ├── 03-testing-iteration/ # Testing strategies
│   ├── 04-distribution-sharing/
│   ├── 05-patterns-troubleshooting/
│   ├── 06-resources-references/
│   └── hands-on-labs/        # 3 hands-on labs (beginner to advanced)
```

## 学习路径

| 步骤 | 内容 | 时间 |
|------|------|------|
| 1 | [快速入门](QUICKSTART.md) -- 复制 hello-world，看它触发 | 5 分钟 |
| 2 | [工坊第 1 章](skills-workshop/01-fundamentals/slides.md) -- 理解渐进式加载 | 60 分钟 |
| 3 | [实验 1](skills-workshop/hands-on-labs/LAB1-SIMPLE-SKILL.md) -- 构建一个真正的 Skill | 30 分钟 |
| 4 | 浏览 `skills/skills/` -- 学习生产级模式 | 自定进度 |
| 5 | [完整工坊](skills-workshop/README.md) -- 完成全部培训 | 6 小时 |

## 平台兼容性

本仓库的 Skills **天然可移植**：只使用 [Agent Skills 规范](https://agentskills.io/specification) 的标准字段（`name`、`description`、`license`、`metadata`），不含平台私有扩展。任何实现该规范的代理都可以加载它们。已验证或有官方文档支持的平台：

| 平台 | 安装位置 | 文档 |
|------|----------|------|
| **Kiro IDE** | `~/.kiro/skills/`（全局）或 `.kiro/skills/`（工作区） | [kiro.dev/docs/skills](https://kiro.dev/docs/skills/) |
| **Kiro CLI** | `~/.kiro/skills/` | [kiro.dev/docs/skills](https://kiro.dev/docs/skills/) |
| **Claude Code** | `~/.claude/skills/` 或通过插件市场 | [skills/README.md](skills/README.md) —— 已端到端验证，见 [TESTING.md](TESTING.md) |
| **Claude.ai** | 作为自定义 Skill 上传 | [Claude Skills 指南](https://support.claude.com/en/articles/12512180-using-skills-in-claude) |
| **Claude API** | 通过 Skills API | [Skills API 快速入门](https://docs.claude.com/en/api/skills-guide) |
| **其他兼容规范的代理** | 视平台而定 | [agentskills.io](https://agentskills.io/specification) |

可移植性说明：

- **纯指令型 Skills**（安全 SDLC、金融合规、云架构及大部分工程类 Skills）完全可移植——它们是纯 Markdown，除规范支持外不依赖宿主平台任何能力。
- **捆绑可执行 `scripts/` 的 Skills**（如测试生成器、webapp-testing）额外要求平台允许执行代码并安装各 Skill 声明的依赖。
- 各平台的激活行为可能略有差异（何时匹配 description 由各代理自行决定）；本仓库 Skill 描述中的触发措辞已在 Claude Code 上实测，并遵循 Kiro 官方指南。

## Kiro 特性

### Steering 文件

Kiro 支持在项目根目录的 `.kiro/steering/` 目录中放置 **steering 文件**。这些 Markdown 文件定义了项目范围内的约定、编码标准和行为规则，Kiro 在你的仓库中工作时会遵循这些规则。

本仓库使用 `.kiro/steering/conventions.md` 来确保所有贡献的格式、命名和结构保持一致。

### 项目级 Skills

Skills 可以安装在两个层级：

| 范围 | 位置 | 用例 |
|------|------|------|
| **项目级** | `.kiro/skills/`（提交到仓库） | 与所有贡献者共享；项目特定的工作流 |
| **全局** | `~/.kiro/skills/`（用户主目录） | 个人效率 Skills；跨项目工具 |

项目级 Skills 与代码库一起进行版本控制，克隆仓库的所有人都可以自动使用。

### Kiro Web

[Kiro Web](https://kiro.dev) 提供基于浏览器的访问，包含两种交互模式：

- **Vibe 模式** - 对话式迭代，你和 Kiro 来回交流以优化输出
- **Autonomous 模式** - Kiro 独立完成任务，完成后向你汇报

两种模式都支持 Skills 以提供增强的领域特定辅助。

## 贡献指南

请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解添加新 Skills、代码标准和 Pull Request 流程的指南。

## 持续集成

GitHub Actions 在每次 push 和 pull request 时验证所有 Skills。工作流会检查 SKILL.md 的 frontmatter、必填字段和命名规范。详见 `.github/workflows/validate-skills.yml`。

## 参考文档

- [Agent Skills 规范](https://agentskills.io/specification)
- [Kiro Skills 文档](https://kiro.dev/docs/skills/)
- [Claude Skills 概述](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Claude Skills 最佳实践](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Anthropic Skills 仓库](https://github.com/anthropics/skills)

## 仓库规范

- 不允许 PDF、PPTX、DOCX 或其他二进制文档文件（已在 gitignore 中排除）
- 不允许包含 PII 或客户数据
- 不允许硬编码凭据或密钥
- 所有内容必须使用开源许可（MIT 或 Apache 2.0，见下方说明）

## 许可证

本仓库包含两种开源许可的内容：

| 内容 | 许可证 |
|------|--------|
| 仓库文档、工坊材料、工程类 Skills、工具脚本 | [MIT](LICENSE) |
| 从 [anthropics/skills](https://github.com/anthropics/skills) 引入的示例 Skills（如 skill-creator、mcp-builder、canvas-design） | Apache 2.0 —— 见各 Skill 目录下的 `LICENSE.txt` |

Anthropic 的 source-available 文档类 Skills（docx、pdf、pptx、xlsx）**不**包含在本仓库中，请使用官方 [anthropics/skills](https://github.com/anthropics/skills) 仓库。
