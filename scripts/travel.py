#!/usr/bin/env python3
"""Unified optional CLI for Travel Advisor Skill v2.0 (stdlib only, offline).

Examples:
  python scripts/travel.py --capabilities
  python scripts/travel.py examples/runtime-compare.json --format md
  python scripts/travel.py examples/runtime-export-trip.json --format ics --out trip.ics
  python scripts/travel.py examples/runtime-export-trip.json --format html --out trip.html
  cat payload.json | python scripts/travel.py --stdin --task pass_check --format md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from travel_core.common import InputError, detect_lang
from travel_core.engine import execute


def render_markdown(response, lang='auto'):
    lang = detect_lang(response, lang)
    zh = lang == 'zh'
    task = response.get('task', 'result')
    lines = [f'# Travel Advisor · {task}', '']

    if task == 'compare':
        headers = ('| 选项 | 同口径总价 | 人均 / 每晚 | 条件可比性 | 备注 |' if zh
                   else '| Option | All-in Total | Unit | Comparability | Notes |')
        lines.extend([headers, '|---|---:|---:|---|---|'])
        for item in response['options']:
            if item['quote_normalized']:
                price = f"{item['all_in_price']:.2f} {item.get('currency') or ''}".strip()
                if item.get('fx_converted') and item.get('original_price') is not None:
                    price += f" ({item['original_price']:.2f} {item.get('original_currency') or ''})"
            else:
                price = '待核实' if zh else 'Unverified'
            unit_bits = []
            if item.get('per_night_price') is not None:
                unit_bits.append(f"{item['per_night_price']:.2f}/{'晚' if zh else 'nt'}")
            if item.get('per_person_price') is not None:
                unit_bits.append(f"{item['per_person_price']:.2f}/{'人' if zh else 'pp'}")
            unit = ' · '.join(unit_bits) or '—'
            if item['price_comparable']:
                cond = '✅ 同条件可比' if zh else '✅ Comparable'
            elif item['quote_normalized']:
                cond = '⚠️ 权益不同（单列）' if zh else '⚠️ Distinct terms'
            else:
                cond = '❓ 条件未齐' if zh else '❓ Incomplete'
            notes = ', '.join(item['issues']) or '—'
            lines.append(f"| {item['name']} | {price} | {unit} | {cond} | {notes} |")
        if response.get('fx_as_of'):
            lines.append('')
            lines.append((f"**汇率基准日：** {response['fx_as_of']}（含发卡行点差请以账单为准）" if zh
                          else f"**FX rate date:** {response['fx_as_of']} (card/bank spreads may still apply)"))
        lines.append('')
        lines.append('**备注：** 仅日期、人数、币种与权益一致的报价参与价格排序；权益不同需单独权衡。' if zh
                     else '**Note:** Only quotes with identical dates, occupancy, currency, and entitlements share a price ranking.')

    elif task == 'verify':
        headers = ('| 主张 | 结论 | 独立支持源 | 风险与拦截 |' if zh
                   else '| Claim | Verdict | Independent Support | Flags |')
        lines.extend([headers, '|---|---|---:|---|'])
        for c in response['claims']:
            flags = []
            if c.get('stale_or_undated_sources'):
                flags.append(('检索过期:' if zh else 'stale retrieval:') + ','.join(c['stale_or_undated_sources']))
            if c.get('stale_published_sources'):
                flags.append(('内容过期/无发布日:' if zh else 'stale/undated content:') + ','.join(c['stale_published_sources']))
            if c.get('snippet_only_sources'):
                flags.append(('仅摘要需点开原文:' if zh else 'snippet-only:') + ','.join(c['snippet_only_sources']))
            if c.get('future_dated_sources'):
                flags.append(('未来时间戳异常:' if zh else 'future timestamp:') + ','.join(c['future_dated_sources']))
            lines.append(
                f"| {c['claim']} | {c.get('badge', '❓')} {c['verdict']} | {c['independent_supporting_origins']} | {'; '.join(flags) or '—'} |"
            )

    elif task == 'budget' and 'scenarios' in response:
        cur = response.get('currency', '')
        lines.append((f"**总预算：** {response['budget_total']:.2f} {cur} ｜ **应急备用金：** {response['reserve']:.2f} {cur}" if zh
                      else f"**Total budget:** {response['budget_total']:.2f} {cur} | **Reserve:** {response['reserve']:.2f} {cur}"))
        lines.append('')
        headers = ('| 情景 | 总计 | 弹性体验盘 | 人均 |' if zh
                   else '| Scenario | Total | Flexible Envelope | Per Person |')
        lines.extend([headers, '|---|---:|---:|---:|'])
        labels = {'tight': '精打细算' if zh else 'Tight', 'balanced': '均衡推荐 ⭐' if zh else 'Balanced ⭐', 'upgraded': '体验升级' if zh else 'Upgraded'}
        for key in ('tight', 'balanced', 'upgraded'):
            sc = response['scenarios'][key]
            pp = f"{sc['per_person']:.2f}" if 'per_person' in sc else '—'
            lines.append(f"| {labels[key]} | {sc['total']:.2f} {cur} | {sc['flexible_total']:.2f} {cur} | {pp} |")

    elif task == 'pass_check':
        cur = response.get('currency', '')
        pp = response['per_person']
        verdict_map = {
            'worth_it': '✅ 值得购买' if zh else '✅ Worth buying',
            'marginal_check_convenience': '≈ 接近持平（看便利性）' if zh else '≈ Marginal (weigh convenience)',
            'buy_point_to_point': '❌ 建议单买更划算' if zh else '❌ Buy point-to-point',
            'provisional_unverified_fares': '❓ 票价未全核实（暂定）' if zh else '❓ Provisional (unverified fares)',
        }
        lines.append(f"**{response['pass_name']}** · {verdict_map.get(response['verdict'], response['verdict'])}")
        lines.append('')
        lines.append((f"- 单买合计：{pp['point_to_point_total']:.2f} {cur}" if zh else f"- Point-to-point total: {pp['point_to_point_total']:.2f} {cur}"))
        lines.append((f"- Pass 实际总成本（含附加费与未覆盖路段）：{pp['pass_effective_total']:.2f} {cur}" if zh
                      else f"- Effective pass total (incl. surcharges & excluded legs): {pp['pass_effective_total']:.2f} {cur}"))
        lines.append((f"- 人均净节省：{pp['net_savings_with_pass']:+.2f} {cur}（回本率 {pp['break_even_ratio']:.2f}x）" if zh
                      else f"- Net savings per person: {pp['net_savings_with_pass']:+.2f} {cur} (break-even ratio {pp['break_even_ratio']:.2f}x)"))

    elif task in ('audit', 'plan'):
        if response.get('status') == 'host_agent_planning_required':
            lines.append('**行程生成：** 由宿主 Agent 使用可用实时检索/地图工具执行；本地工具不离线生成行程。' if zh
                         else '**Itinerary planning:** Performed by the host agent with live tools; no offline generator exists.')
            lines.append(f"**{'执行手册' if zh else 'Workflow'}:** {response.get('workflow_reference', 'references/itinerary-and-pacing.md')}")
            return '\n'.join(lines).rstrip() + '\n'
        lines.append(f"**{'整体状态' if zh else 'Overall status'}:** {response.get('overall_status', '—')}")
        for d in response.get('days', []):
            lines.append(f"\n### {d['date']} · {d['status']} ({d.get('pace_level', '—')}, {d.get('scheduled_minutes', 0)} min)")
            for issue in d['issues']:
                target = issue.get('stop_ids', issue.get('stop_id', ''))
                lines.append(f"- [{issue['severity']}] {issue['code']} {target}".rstrip())
        if response.get('interday_checks'):
            lines.append('\n### ' + ('跨天衔接' if zh else 'Interday continuity'))
            for b in response['interday_checks']:
                lines.append(f"- {b['from_date']} → {b['to_date']}: {b['status']}")
                for issue in b['issues']:
                    lines.append(f"  - [{issue['severity']}] {issue['code']}")
        if response.get('reservations_pending'):
            lines.append('\n### ' + ('待确认预约' if zh else 'Pending reservations'))
            for r in response['reservations_pending']:
                lines.append(f"- {r['date']} · {r['name']} (lead_days={r.get('lead_days', '?')})")
        cost_check = response.get('cost_check')
        if cost_check:
            lines.append(f"\n### {'费用检查' if zh else 'Cost check'}: {cost_check.get('status', 'unknown')}")
            if cost_check.get('unpriced_categories'):
                lines.append(('未报价类别：' if zh else 'Unpriced categories: ') + ', '.join(cost_check['unpriced_categories']))
            if cost_check.get('missing_required_categories'):
                lines.append(('缺失必要类别：' if zh else 'Missing required categories: ') + ', '.join(cost_check['missing_required_categories']))
    else:
        lines.append('```json')
        lines.append(json.dumps(response, ensure_ascii=False, indent=2))
        lines.append('```')

    return '\n'.join(lines).rstrip() + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description='Travel Advisor Skill v2.0 deterministic offline CLI')
    parser.add_argument('input', nargs='?', help='JSON task file (omit with --capabilities or --stdin)')
    parser.add_argument('--stdin', action='store_true', help='Read JSON payload from stdin')
    parser.add_argument('--task', help='Override or supply task name in the payload')
    parser.add_argument('--capabilities', action='store_true', help='Display zero-config offline & host boundaries')
    parser.add_argument('--format', choices=('json', 'md', 'ics', 'html'), default='json')
    parser.add_argument('--lang', choices=('auto', 'zh', 'en'), default='auto')
    parser.add_argument('--out', type=Path, help='Write output to file (defaults to stdout)')
    args = parser.parse_args(argv)

    try:
        if args.capabilities:
            result = execute({'task': 'capabilities'}, lang=args.lang)
        else:
            if args.stdin:
                raw_text = sys.stdin.read()
            elif args.input:
                raw_text = Path(args.input).read_text(encoding='utf-8')
            else:
                parser.error('Specify a JSON task file, --stdin, or --capabilities')
            payload = json.loads(raw_text)
            if args.task:
                payload['task'] = args.task
            elif args.format == 'ics' and 'task' not in payload:
                payload['task'] = 'export_ics'
            elif args.format == 'html' and 'task' not in payload:
                payload['task'] = 'export_html'
            result = execute(payload, lang=args.lang)

        if args.format == 'ics':
            if 'ics' not in result:
                raise InputError('--format ics requires task=export_ics')
            text = result['ics']
        elif args.format == 'html':
            if 'html' not in result:
                raise InputError('--format html requires task=export_html')
            text = result['html']
        elif args.format == 'md':
            text = render_markdown(result, lang=args.lang)
        else:
            text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'

        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text, encoding='utf-8')
            print(f'Wrote {args.out}', file=sys.stderr)
        else:
            sys.stdout.write(text)
        return 0
    except (InputError, ValueError, OSError, KeyError, TypeError) as exc:
        print(
            json.dumps({'status': 'error', 'error_type': type(exc).__name__, 'message': str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
