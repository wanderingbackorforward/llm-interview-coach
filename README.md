# llm-interview-coach

> 大模型应用岗面试私教 Skill（Claude Code SKILL.md 规范）

**简历中心** · **五模式**（精讲/严厉测试/模拟面试+复盘/填鸭/简历深挖） · **大厂真实面经驱动** · **动态调速** · **主动拉回走神** · **绝无臆造**

## 这是什么

一个基于 Claude Code [Agent Skills 规范](https://github.com/anthropics/skills) 的面试辅导 skill。
不是静态八股笔记，是一个**真正的私教引擎**——五模式随时切换，进度自动持久化，能力自动调速。

**目标**：让用户**真的学会并扛过面试**，不是把资料念一遍。

## 五模式一览

| 模式 | 用途 | 步骤上限 |
|---|---|---|
| **精讲** | 5 台阶讲透一个知识点，举一反三 | 5 台阶/知识点 |
| **严厉测试** | 出题→判分→3 轮逼近答案 | 3 轮/题 |
| **模拟面试+复盘** | 扮面试官按真实面经开+追问，结束 3 层复盘 | 5-7 问/场 |
| **填鸭背诵** | 20 题快背最高频考点，抽查默写 | 20 题/轮 |
| **简历深挖** | 选 1 简历项目连环追问 5-8 层 | 1 项目 5-8 层 |

## 快速使用

### 1. 安装到 Claude Code
把这个仓库 `git clone` 到 Claude Code 的 skills 目录：

```bash
git clone https://github.com/wanderingbackorforward/llm-interview-coach.git \
  ~/.claude/skills/llm-interview-coach
```

### 2. 配置学习资料路径
本 skill 默认假设有一份本地学习资料目录（按方向切好的 markdown），需要用户配置。

**方式 A：替换占位符**
在所有 `.md` 文件里把 `<YOUR_LEARNING_MATERIALS_DIR>` 替换为你的实际路径。

**方式 B：创建符号链接**（推荐）
把包含 `md_split/` 和 `试卷/` 的目录软链接到 `<YOUR_LEARNING_MATERIALS_DIR>`。

skill 通过 `references/知识图谱.md` 索引学习资料的目录结构。如果你的资料结构不同，请相应修改知识图谱。

### 3. 触发 skill
在 Claude Code 中描述你想学的内容，skill 自动启动。例：
- "讲讲 MCP 协议"
- "考考我 Agent 框架"
- "模拟面字节抖音 Agent"
- "深挖我简历上的 RAG 项目"

## 核心文件

| 文件 | 作用 |
|---|---|
| `SKILL.md` | skill 主入口，五模式路由、铁律、启动流程、状态判断 |
| `references/模式工作流.md` | 五模式的详细步骤化工作流（进入模式前必读） |
| `references/知识图谱.md` | 19 方向 × 45 知识点 × md 文件路径的完整映射 + 高频考点排序 |
| `references/面经库.md` | 真实面经索引（公司/岗位/问过的问题/复盘要点） |
| `progress.json` | 学习进度持久化（启动时 Read，每节结束写回） |

## 设计原则（六条铁律）

1. **内容只认学习资料，绝不臆造**——读不到就说没有。
2. **`progress.json` 是唯一记忆**——绝不凭印象记进度。
3. **节奏服务于"学会"**——一次一台阶，讲完停问。
4. **课表是活的**——随情绪/能力/互动/简历动态调整。
5. **绝不沉默等待**——走神/不答/敷衍时主动拉回。
6. **简历中心**——简历项目/技能最高优先。

## 与静态笔记型面试题库的区别

| 维度 | 静态题库 | 本 skill |
|---|---|---|
| 互动 | 无 | 五模式+动态调速 |
| 进度追踪 | 无 | `progress.json` 全自动 |
| 简历挂钩 | 无 | 简历深挖模式 + 简历中心排课 |
| 模拟面试 | 无 | 还原真实压力+3 层复盘 |
| 大厂面经 | 部分有 | 精讲/测试/填鸭每环节强制挂钩 |
| 走神/沮丧应对 | 无 | 主动拉回+共情+严厉督促 |

## 借鉴过的项目

- [anthropics/skills](https://github.com/anthropics/skills) — Claude Code SKILL.md 规范
- [wdndev/llm_interview_note](https://github.com/wdndev/llm_interview_note) — 大模型面试笔记结构参考
- [ComposioHQ/awesome-claude-skills](https://github.com/ComposioHQ/awesome-claude-skills) — 社区 skill 设计模式

## License

MIT
