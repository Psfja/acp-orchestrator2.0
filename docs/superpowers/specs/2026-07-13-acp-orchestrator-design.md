# ACP Orchestrator — 多 Agent 编排框架设计规格

## 概述

基于 ACP (Agent Client Protocol) 的多 Agent 协作编排框架。编排 Agent 拆分任务，中间脚本通过 ACP 协议路由给执行 Agent，检查 Agent 审核，测试 Agent 验证，不通过则回到编排阶段重新迭代，形成闭环直到项目通过。

## 核心约束

- 执行 Agent 之间互不通信，完全隔离
- 所有通信通过 ACP 协议（stdin/stdout 子进程模式）
- Agent 不通过注册配置，直接用 ACP 调用已安装的 Agent
- 在 agents.yaml 中定义每个 Agent 的专长和提示词规范
- 所有编排→执行→检查→测试的消息实时终端可见
- 编排 Agent 本身也是标准 ACP Agent，可替换

## 架构：状态机 + 事件驱动任务队列

### 核心组件

#### 1. Agent Manager（Agent 生命周期管理）
- 职责：管理 ACP Agent 子进程的 spawn/kill/stdin/stdout
- 从 agents.yaml 读取配置（启动命令、角色、系统提示词）
- 提供统一接口：`spawn()`, `send_task()`, `read_response()`, `kill()`
- 不关心任务内容，只负责进程管理

#### 2. Task Queue（任务队列）
- 职责：管理任务的入队、分发、状态追踪
- 支持任务依赖关系（B 等待 A 完成）
- 提供进度摘要：`[████░░] 3/4 完成`
- 不关心谁来执行

#### 3. FSM Engine（状态机核心）
- 职责：掌控整个编排流程的状态转换
- 7 个状态：IDLE → ORCHESTRATING → DISPATCHING → EXECUTING → REVIEWING → TESTING → COMPLETED
- 1 个终止状态：FAILED
- 返工路径：REVIEWING → ORCHESTRATING、TESTING → ORCHESTRATING
- 依赖 AgentManager、TaskQueue、Logger

#### 4. Logger（日志系统）
- 职责：统一日志格式，实时终端输出
- 格式：`[时间] [来源→目标] [状态] 消息内容`
- 颜色编码区分消息来源（编排/脚本/执行/检查/测试/错误）
- 不参与业务逻辑

### 状态转换表

```
IDLE           → ORCHESTRATING    (用户输入)
ORCHESTRATING  → DISPATCHING      (拆分成功)
ORCHESTRATING  → FAILED           (解析失败×3)
DISPATCHING    → EXECUTING        (任务已分发)
EXECUTING      → REVIEWING        (全部完成)
EXECUTING      → ORCHESTRATING    (有任务失败，返工)
EXECUTING      → FAILED           (超时/崩溃)
REVIEWING      → TESTING          (检查通过)
REVIEWING      → ORCHESTRATING    (不通过，返工)
TESTING        → COMPLETED        (测试通过)
TESTING        → ORCHESTRATING    (不通过，返工)
COMPLETED      → IDLE             (清理)
```

### 循环迭代机制

1. 检查/测试不通过 → 收集失败上下文
2. `rebuild_context()` 组装：原始需求 + 已完成任务列表 + 失败详情
3. 回到 ORCHESTRATING，编排 Agent 看到完整状态
4. 编排 Agent 只拆分需要修复的新任务，已完成的不重复分配
5. 迭代计数器递增，达到上限（默认5轮）→ FAILED

## ACP 通信适配层

### 设计模式

抽象基类 `ACPAdapter`，定义 6 个核心方法：
- `get_launch_command()` → 返回启动命令
- `spawn()` → 启动子进程，返回 stdin/stdout 管道
- `initialize()` → ACP 握手 + 创建会话 + 注入 systemPrompt
- `send_prompt()` → 发送 session/prompt
- `read_updates()` → 流式读取 session/update
- `close_session()` → 关闭会话

### 支持的 Agent

所有支持 ACP 协议的主流 Agent。新增 Agent 只需在 agents.yaml 中添加配置 + 必要时实现一个薄适配器。

| Agent | 启动命令 | 适配器类 | 备注 |
|---|---|---|---|
| Claude Code | `claude-code-acp` | `ClaudeCodeAdapter` | Anthropic，社区适配器 |
| Codex CLI | `npx @zed-industries/codex-acp` | `CodexAdapter` | OpenAI，官方适配器 |
| Gemini CLI | `gemini --acp` | `GeminiAdapter` | Google，原生 ACP |
| GitHub Copilot | `copilot --acp` | `CopilotAdapter` | GitHub，原生 ACP |
| Goose | `goose acp` | `GooseAdapter` | Block，原生 ACP |
| Cline | `cline acp` | `ClineAdapter` | 原生 ACP |
| Auggie CLI | `auggie acp` | `AuggieAdapter` | Augment Code |
| Kiro CLI | `kiro-cli acp` | `KiroAdapter` | AWS，原生 ACP |
| OpenCode | `opencode acp` | `OpenCodeAdapter` | 开源，原生 ACP |
| Qwen Code | `qwen-code acp` | `QwenCodeAdapter` | 阿里，多语言支持 |
| Mistral Vibe | `vibe-acp` | `VibeAdapter` | Mistral，轻量级 |
| Factory Droid | `droid acp` | `DroidAdapter` | Factory，自动代码生成 |
| Qoder CLI | `npx @qoder-ai/qodercli --acp` | `QoderAdapter` | Qoder AI |
| Hermes Agent | `hermes acp` | `HermesAdapter` | Nous Research |
| Pi | `pi-acp` | `PiAdapter` | 极简 Agent，社区适配器 |
| Reasonix | `npx reasonix --acp` | `ReasonixAdapter` | DeepSeek 原生，前缀缓存优化 |
| OpenHands | `openhands acp` | `OpenHandsAdapter` | ACP 兼容 |

## 配置文件：agents.yaml

```yaml
settings:
  max_iterations: 5
  task_timeout_seconds: 300
  global_timeout_seconds: 3600

agents:
  orchestrator:
    name: "编排Agent"
    command: "claude-code-acp"
    adapter: "claude_code"
    role: "orchestrator"
    system_prompt: |
      你是项目编排专家。你只做一件事：
      1. 接收用户需求
      2. 分析需要完成的任务
      3. 将任务拆分为独立的子任务
      4. 每个子任务指定由哪个Agent执行
      输出必须是严格的JSON数组格式: [{"id":"task_1","description":"...","assigned_agent":"..."}]
      不要做任何执行工作，只拆分和指派。

  frontend-dev:
    name: "前端开发"
    command: "codex acp"
    adapter: "codex"
    role: "executor"
    system_prompt: |
      你是前端开发专家。你只负责HTML/CSS/JavaScript代码编写。
      不要做后端、数据库相关工作。完成后说明创建/修改了哪些文件。

  backend-dev:
    name: "后端开发"
    command: "claude-code-acp"
    adapter: "claude_code"
    role: "executor"
    system_prompt: |
      你是后端开发专家。你只负责API接口开发和业务逻辑实现。
      不要做前端UI工作。完成后说明创建/修改了哪些文件。

  checker:
    name: "代码审查"
    command: "gemini --acp"
    adapter: "gemini"
    role: "checker"
    system_prompt: |
      你是代码审查专家。你只负责检查代码质量和完整性。
      输出: "通过" 或 "不通过: 具体问题描述"。不要修改代码。

  tester:
    name: "测试"
    command: "codex acp"
    adapter: "codex"
    role: "tester"
    system_prompt: |
      你是测试专家。你只负责编写测试用例、运行测试、报告结果。
      不要修改业务代码。
```

## 错误处理

### 可恢复错误 → 返工
- 检查不通过 → 带问题描述回到 ORCHESTRATING
- 测试不通过 → 带失败测试详情回到 ORCHESTRATING
- 单个任务失败 → 其余继续，失败的回到 ORCHESTRATING

### 不可恢复错误 → FAILED
- 超过最大迭代次数（默认5轮）
- Agent 崩溃且无法恢复
- 编排 Agent 输出持续无法解析（重试3次后）

### 超时保护
- 每个 Agent 任务可配置超时时间（默认300秒）
- 全局流程最大执行时间（默认3600秒）
- 超时任务标记失败，不影响其他任务

## 技术选型

- **语言**：Python 3.11+
- **异步**：asyncio（原生子进程管理 + 并行任务）
- **ACP SDK**：`agent-client-protocol`（Pydantic 模型）
- **配置解析**：PyYAML
- **目标平台**：OpenHands 插件

## 项目结构

```
acp-orchestrator/
├── agents.yaml
├── pyproject.toml
├── src/
│   ├── main.py                 # CLI 入口
│   ├── config/loader.py        # 加载 agents.yaml
│   ├── fsm/
│   │   ├── engine.py           # OrchestrationFSM 核心
│   │   ├── states.py           # 状态枚举 + 转换表
│   │   └── context.py          # rebuild_context()
│   ├── agents/
│   │   ├── manager.py          # AgentManager
│   │   ├── adapter.py          # ACPAdapter 抽象基类
│   │   ├── adapters/           # 各 Agent 适配器 (按需添加)
│   │   │   ├── claude_code.py
│   │   │   ├── codex.py
│   │   │   ├── gemini.py
│   │   │   ├── copilot.py
│   │   │   ├── goose.py
│   │   │   ├── cline.py
│   │   │   ├── auggie.py
│   │   │   ├── kiro.py
│   │   │   ├── opencode.py
│   │   │   ├── qwen_code.py
│   │   │   ├── vibe.py
│   │   │   ├── droid.py
│   │   │   ├── qoder.py
│   │   │   ├── hermes.py
│   │   │   ├── pi.py
│   │   │   ├── reasonix.py
│   │   │   └── openhands.py
│   │   └── session.py          # AgentSession
│   ├── tasks/
│   │   ├── queue.py            # TaskQueue
│   │   └── models.py           # Task, TaskStatus
│   ├── logger/logger.py        # Logger
│   └── openhands/plugin.py     # OpenHands 插件入口
└── tests/
```

## 实现路线

### Phase 1：核心骨架（MVP）
目标：打通最简流程 — 1个编排 Agent + 1个执行 Agent
- 基础组件：config loader, ACPAdapter 抽象, Manager, TaskQueue, Logger
- FSM 线性流程（先不做返工循环）
- CLI 入口

### Phase 2：循环迭代 + 多 Agent
目标：支持返工循环 + 多个执行 Agent 并行
- rebuild_context() + REVIEWING→ORCH 和 TESTING→ORCH 返工路径
- 并行 spawn 多个执行 Agent
- 迭代计数 + 上限保护 + 超时处理

### Phase 3：多 Agent 适配 + 健壮性
目标：支持所有主流 ACP Agent + 完整容错
- 全部适配器实现
- Agent 崩溃重启 + 全局超时
- FAILED 状态完整处理

### Phase 4：OpenHands 集成
目标：作为 OpenHands 插件运行
- OpenHands 插件入口 + UI 集成
- 集成测试 + 文档
