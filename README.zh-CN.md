# Travel Advisor · 智能旅行顾问 (v2.0)

一个**证据优先、强调实时性与真实性**的全能自由行策划 Agent Skill —— 融合专业旅行规划方法论、多源查证战术、高信息密度决策模板，以及零配置纯标准库的可选计算与导出工具。

[English](README.md) · [Skill 入口](SKILL.md) · [使用示例](examples/agent-use-cases.md) · [架构说明](docs/architecture.md) · [更新日志](CHANGELOG.md)

## v2.0 核心特性

- **实时性与真实性硬保障**：价格、税费、汇率、营业与闭馆时间、临时休馆/施工公告、交通时刻、放票规则、签证入境政策一律要求在当前会话通过宿主实时工具核验，**绝不用模型记忆替代时变事实**；强制区分发布日期与检索日期，高风险运营规则拒绝仅凭搜索摘要下结论。
- **四态溯源标签（`✅ / ≈ / ⚠️ / ❓`）**：所有关键结论与导出文件均清晰区分“本次实查已核实”“估算口径”“来源冲突或过期”和“待核实”，绝不把未查证猜测伪装成确定信息。
- **按需加载的旅行专家方法论**：保持入口极简，按任务按需读取专业手册：
  - **行程与节奏**：片区聚类防折返、到达/返程留白、体力波动曲线、星期闭馆与当地节假日排雷、预约抢票倒计时、同片区雨天/排队 Plan B。
  - **选址与交通**：商圈枢纽半径与噪音/近期差评排雷、换酒店隐性损耗、高铁 vs 飞机门到门总耗时、交通 Pass/城市卡回本测算、隐性税费（城市税/度假村费/行李费）与多币种同口径比价。
  - **预算与权衡**：固定项 + 应急备用金 + 三档情景（精打细算 / 均衡推荐 / 体验升级）、Top 2 成本杠杆、用“决策翻转条件”代替伪精确打分、多人公平性保护。
  - **人群与跨境**：亲子、长辈无障碍、多人小团“核心共游 + 同片区分头窗口”、独行安全，以及官方签证/护照/支付/网络与按需行前清单。
- **清晰直观的实用交付物**：统一精炼的对话对比表与日程表、多轮讨论防漂移的 `Trip State` 快照，以及按需生成的 **`.ics` 日历文件** 和 **离线单文件 HTML 行程单/对比卡**（方便手机查看和发给同行人）。
- **克制边界与用户主导**：只做用户要求的部分，缺关键信息时一次最多问 1 个决定性问题，局部修改严守已锁定/已预订安排。

## 安装

将本仓库放入 Agent 的 Skills 目录即可。**无需 API Key、无需环境变量、不依赖第三方 Python 包。**

### Codex / Antigravity / 其他兼容 Agent Skills 的宿主

```bash
git clone https://github.com/Asahi230035/travel-advisor-skill.git
mkdir -p ~/.agents/skills/travel-advisor
cp -R travel-advisor-skill/. ~/.agents/skills/travel-advisor/
```

若仅在某个项目中使用，可放到 `.agents/skills/travel-advisor/`；Claude Code 可放到 `.claude/skills/travel-advisor/`。

入口文件为 [`SKILL.md`](SKILL.md)，安装后直接用自然语言提问即可。

## 使用示例

- **酒店比价与排雷**：*“帮我对比 12/4–12/6 新宿站附近三家酒店（2 成人），重点看安静度、机场接驳和含税总价。”*
- **攻略实效核验**：*“这篇 2024 年攻略说博物馆周一开门且不用预约，帮我查证现在还准不准。”*
- **交通 Pass 回本测算**：*“东京-京都-大阪 6 天，买 7 日 JR Pass 划不划算？”*
- **预算与杠杆分析**：*“4 个人去成都 3 天，总预算 8000，重美食和住宿，给我几档方案。”*
- **局部审查与修改**：*“看看第二天是不是太赶，把下午换成喝茶；第三天已经订票不要动。”*
- **规划并导出**：*“帮我们 4 个人（含 1 位长辈）规划 3 天轻松游，定稿后导出 `.ics` 日历和一个手机能直接打开的 HTML 行程单。”*

更多示例参见 [使用场景](examples/agent-use-cases.md)。

## 项目结构

```text
travel-advisor-skill/
├── SKILL.md                 # 精简入口、实时性红线与按需加载索引
├── references/              # 核心规范与四大领域专家手册（7 份）
├── travel_core/             # 可选纯标准库计算、核验、审计与导出引擎
├── scripts/travel.py        # 统一可选 CLI（支持 --stdin、json/md/ics/html、中英切换）
├── schemas/                 # 结构化数据参考定义
├── examples/                # 模拟测试样例与真实对话范例
├── evals/scenarios.md       # 24 个带 Rubric 评分标准的 Agent 行为评测集
├── tests/                   # 自动化单元测试、安全转义与仓库契约测试
└── docs/                    # 架构、设计、使用与评测文档
```

**边界说明**：实时查证与行程编排始终由宿主 Agent 调用自身可用工具完成；本地可选脚本**不联网、不预订、也绝不离线生成行程**。

## 开发与测试

运行全量自动化测试：

```bash
python3 -m unittest discover -s tests -v
```

体验统一离线命令行工具（示例均为模拟数据）：

```bash
python3 scripts/travel.py --capabilities
python3 scripts/travel.py examples/runtime-compare.json --format md
python3 scripts/travel.py examples/runtime-verify.json --format md
python3 scripts/travel.py examples/runtime-budget.json --format md
python3 scripts/travel.py examples/runtime-pass-check.json --format md
python3 scripts/travel.py examples/runtime-export-trip.json --format html --out /tmp/trip.html
python3 scripts/travel.py examples/runtime-export-trip.json --task export_ics --format ics --out /tmp/trip.ics
```

更多说明见 [评测指南](docs/evaluation.md) 和 [使用说明](docs/usage.md)。

## 开源协议

本项目采用 [MIT License](LICENSE)。安全问题反馈请参考 [SECURITY.md](SECURITY.md)。
