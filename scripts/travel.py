#!/usr/bin/env python3
"""Optional Travel Advisor validators. Usage: python scripts/travel.py examples/runtime-compare.json

Input is JSON; result is JSON or a human-readable Markdown summary.
The host AI agent is responsible for research/generation and user interaction.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from travel_core.engine import execute
from travel_core.common import InputError


def render_markdown(response):
    task = response.get('task', 'result')
    lines = [f'# Travel Advisor Skill · {task}', '']
    if response.get('status') == 'needs_clarification':
        question = response.get('question', {})
        lines += [f"需要确认：{question.get('question','请补充信息')}", '']
    elif task == 'compare':
        lines.extend(['| 选项 | 报价总额 | 条件可比性 | 备注 |', '|---|---:|---|---|'])
        for item in response['options']:
            price = (f"{item['all_in_price']:.2f} {item.get('currency') or ''}"
                     if item['quote_normalized'] else '待核实')
            condition = ('同条件报价' if item['price_comparable'] else
                         '仅单项报价；无等价对照' if item['quote_normalized'] else '报价条件未核实')
            lines.append(f"| {item['name']} | {price} | {condition} | {', '.join(item['issues']) or '—'} |")
        lines += ['', '**备注：** 只有日期、人数、房型及权益一致的报价才参与同组价格排名；权益不同应单独比较取舍。']
    elif task in ('audit', 'plan'):
        if response.get('status') == 'host_agent_planning_required':
            lines.append('**行程生成：** 由宿主 Agent 使用可用的联网与地图工具执行；本地工具不生成旅行方案。')
            lines.append(f"**执行规则：** {response.get('workflow_reference', 'references/itinerary-planning.md')}")
            return '\n'.join(lines).rstrip() + '\n'
        lines.append(f"**整体检查状态：** {response.get('overall_status','—')}")
        for d in response.get('days', []):
            lines.append(f"\n### {d['date']} · {d['status']}")
            for issue in d['issues']:
                lines.append(f"- [{issue['severity']}] {issue['code']} {issue.get('stop_ids',issue.get('stop_id',''))}")
        if response.get('interday_checks'):
            lines.append('\n### 跨天衔接')
            for boundary in response['interday_checks']:
                lines.append(f"- {boundary['from_date']} → {boundary['to_date']}：{boundary['status']}")
                for issue in boundary['issues']:
                    lines.append(f"  - [{issue['severity']}] {issue['code']}")
        cost_check = response.get('cost_check')
        if cost_check:
            lines.append(f"\n### 费用检查：{cost_check.get('status', 'unknown')}")
            if cost_check.get('unpriced_categories'):
                lines.append('未报价类别：' + '、'.join(cost_check['unpriced_categories']))
            if cost_check.get('missing_required_categories'):
                lines.append('未覆盖必要类别：' + '、'.join(cost_check['missing_required_categories']))
    elif task == 'verify':
        for c in response['claims']:
            lines.append(f"- **{c['claim']}**：{c['verdict']}（独立支持来源 {c['independent_supporting_origins']}）")
    else:
        lines.append('```json')
        lines.append(json.dumps(response, ensure_ascii=False, indent=2))
        lines.append('```')
    return '\n'.join(lines).rstrip() + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description='Travel Advisor Skill: safe deterministic travel decisions')
    parser.add_argument('input', nargs='?', help='JSON task file; omit with --capabilities')
    parser.add_argument('--capabilities', action='store_true', help='Display zero-config offline and host-tool capabilities')
    parser.add_argument('--format', choices=('json', 'md'), default='json')
    parser.add_argument('--out', type=Path, help='Write result to file (defaults to stdout)')
    args = parser.parse_args(argv)
    try:
        if args.capabilities:
            result = execute({'task': 'capabilities'})
        else:
            if not args.input:
                parser.error('Specify a JSON task file or --capabilities')
            payload = json.loads(Path(args.input).read_text(encoding='utf-8'))
            result = execute(payload)
        text = render_markdown(result) if args.format == 'md' else json.dumps(result, ensure_ascii=False, indent=2) + '\n'
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text, encoding='utf-8')
            print(f'Wrote {args.out}', file=sys.stderr)
        else:
            sys.stdout.write(text)
        return 0
    except (InputError, ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'status':'error','error_type':type(exc).__name__,
                          'message':str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
