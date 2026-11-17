# Travel Advisor · 智能旅行顾问

一个用于旅行信息检索、方案比较、预算分析和行程规划的 Agent Skill，支持多源核验与个性化建议。

[English](README.md) · [Skill 入口](SKILL.md) · [使用示例](examples/agent-use-cases.md) · [架构说明](docs/architecture.md) · [参与贡献](CONTRIBUTING.md)

## 功能特性

- **旅行目的地发现**：根据兴趣、预算和出行限制筛选目的地、景点、餐厅与活动。
- **信息核验**：结合可靠来源核实攻略、开放时间和出行提示，识别过时或冲突的信息。
- **多方案比较**：对齐日期、人数、交通时刻、换乘、行李、房型、税费、早餐、支付与退改条件，比较酒店、交通及活动选择。
- **预算管理**：在必要支出和备用金的基础上，按照用户偏好合理倾斜，兼顾整体旅行体验。
- **行程规划**：需要时由宿主 Agent 检索真实地点、交通及开放时间，再编排行程；不依赖本地离线规划算法。
- **行程审查**：检查访问顺序、跨天交通衔接、时间冲突、预算缺口、预约要求及执行风险。
- **个性化评价**：结合个人或多人偏好评估备选方案，并解释不同选择的取舍。
- **局部调整**：修改酒店、景点或某一天的安排，尽量保留已确定的其他内容。

既可以只解决一个局部问题，也可以规划完整旅行。Skill 会根据当前任务选择必要的能力，并仅在关键信息不足时主动反问。

## 安装

将本仓库放入 Agent 的 Skills 目录即可。Skill 本身无需 API Key，也不依赖第三方 Python 包。

### Codex

```bash
git clone https://github.com/USERNAME/travel-advisor-skill.git
mkdir -p ~/.agents/skills/travel-advisor
cp -R travel-advisor-skill/. ~/.agents/skills/travel-advisor/
```

**说明：** 仓库发布后，将 `USERNAME` 替换为实际 GitHub 用户名；如果已经下载仓库，可跳过 `git clone`。

若仅在某个项目中使用，也可将目录放到 `.agents/skills/travel-advisor/`。其他兼容 Agent Skills 的工具使用各自的 Skill 目录，例如 Claude Code 的 `.claude/skills/travel-advisor/`。

入口文件为 [`SKILL.md`](SKILL.md)。安装后直接向 Agent 提出旅行问题即可；部分宿主也支持显式调用 `$travel-advisor`。

## 使用示例

**酒店比较**

> 帮我对比新宿站附近的三家酒店，重点比较交通、房间面积和退改政策。

**攻略核验**

> 帮我核实这篇网上攻略的景点开放时间是否准确。

**预算分配**

> 四个人去成都玩，总预算 5000 元，比较重视住宿和美食，但整体体验也要均衡。

**行程审查**

> 看看我第二天的安排是不是太赶，其他几天先不要动。

**完整规划**

> 帮我们规划成都五日轻松游，重点是美食、人文和少量二次元相关地点。

更多示例参见 [使用场景](examples/agent-use-cases.md)。

## 工作流程

1. **识别任务**：确定用户当前要解决的问题、预算、偏好和已确认的安排。
2. **必要反问**：只有缺失信息可能改变结果时才继续询问。
3. **按需检索**：使用宿主 Agent 已提供的网页、地图等工具获取相关信息。
4. **比较与验证**：对齐候选条件，分析优缺点并检查硬约束。
5. **输出结果**：呈现适合当前任务的结论、证据、风险与待确认事项。
6. **局部更新**：用户修改要求时，只重新处理受影响的部分。

Skill 会区分已核实事实、估算、主观体验和未知信息。实时价格和交通数据的可访问性取决于宿主已有工具与可获取来源。**行程由宿主 Agent 基于查得的资料编排，而不是由离线规划算法自动生成。**

## 项目结构

```text
travel-advisor-skill/
├── SKILL.md              # Skill 入口与执行规则
├── references/           # 各类任务的具体规范
├── travel_core/          # 可选的 Python 确定性计算模块
├── scripts/              # 可选命令行入口
├── schemas/              # 结构化数据定义
├── examples/             # 使用示例与模拟数据
├── evals/                # Agent 行为评估用例
├── tests/                # 自动化回归测试
└── docs/                 # 架构及开发文档
```

Skill 优先利用 Agent 已有的工具能力；随附的 Python 计算脚本是可选的，且仅使用标准库。这些脚本可以校验已有行程，但不会离线生成行程。具体规则参见 [行程规划流程](references/itinerary-planning.md)。

## 开发与测试

运行测试：

```bash
python -m unittest discover -s tests -v
```

查看离线计算工具：

```bash
python scripts/travel.py --capabilities
python scripts/travel.py examples/runtime-compare.json --format md
```

仓库中的示例价格和评分均为模拟测试数据，不代表实时报价或实际预订结果。更多信息见 [测试说明](docs/evaluation.md) 和 [贡献指南](CONTRIBUTING.md)。

## 开源协议

本项目采用 [MIT License](LICENSE)。安全问题反馈请参考 [SECURITY.md](SECURITY.md)。
