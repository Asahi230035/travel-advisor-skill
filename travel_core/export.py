"""Pure-stdlib practical exporters: RFC 5545 .ics calendar & single-file offline HTML.

Preserves verification provenance badges (verified / estimate / conflict / unverified)
so exported artifacts never disguise unverified drafts as confirmed bookings.
"""
from __future__ import annotations

from datetime import datetime, timezone
import html

from .common import InputError, clock, date_value, detect_lang, require_dict, require_list

BADGE_MAP = {
    'verified': ('✅', '已核实', 'Verified', 'badge-ok'),
    'estimate': ('≈', '估算', 'Estimate', 'badge-est'),
    'conflict': ('⚠️', '冲突/过期', 'Conflict/Stale', 'badge-warn'),
    'stale': ('⚠️', '冲突/过期', 'Conflict/Stale', 'badge-warn'),
    'unverified': ('❓', '待核实', 'Unverified', 'badge-unk'),
}


def _badge_info(status, lang):
    key = str(status or 'unverified').lower()
    icon, zh_label, en_label, css = BADGE_MAP.get(key, BADGE_MAP['unverified'])
    return icon, (zh_label if lang == 'zh' else en_label), css


def _ics_escape(text):
    return (
        str(text)
        .replace('\\', '\\\\')
        .replace(';', '\\;')
        .replace(',', '\\,')
        .replace('\r\n', '\\n')
        .replace('\n', '\\n')
    )


def _ics_fold(line):
    """Fold RFC 5545 lines at 75 octets."""
    encoded = line.encode('utf-8')
    if len(encoded) <= 75:
        return line
    chunks = []
    cur = bytearray()
    limit = 75
    for ch in line:
        b = ch.encode('utf-8')
        if len(cur) + len(b) > limit:
            chunks.append(cur.decode('utf-8'))
            cur = bytearray(b' ' + b)
            limit = 75
        else:
            cur.extend(b)
    if cur:
        chunks.append(cur.decode('utf-8'))
    return '\r\n'.join(chunks)


def _fmt_dt_local(day_str, hhmm):
    d = date_value(day_str, 'day.date')
    mins = clock(hhmm, 'stop.time')
    return f'{d.strftime("%Y%m%d")}T{mins // 60:02d}{mins % 60:02d}00'


def export_ics(payload, lang='auto'):
    """Export a trip draft/plan JSON into an RFC 5545 .ics calendar string."""
    require_dict(payload)
    lang = detect_lang(payload, lang)
    title = payload.get('title') or ('旅行行程' if lang == 'zh' else 'Travel Itinerary')
    tzid = payload.get('timezone')
    days = require_list(payload.get('days'), 'days', nonempty=True)
    dtstamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')

    lines = [
        'BEGIN:VCALENDAR',
        'VERSION:2.0',
        'PRODID:-//Travel Advisor Skill//v2.0//EN',
        'CALSCALE:GREGORIAN',
        f'X-WR-CALNAME:{_ics_escape(title)}',
    ]
    if tzid:
        lines.append(f'X-WR-TIMEZONE:{_ics_escape(tzid)}')

    event_count = 0
    for day in days:
        require_dict(day, 'day')
        day_str = day.get('date')
        date_value(day_str, 'day.date')
        stops = require_list(day.get('stops', []), 'day.stops')
        for idx, stop in enumerate(stops):
            require_dict(stop, 'stop')
            name = stop.get('name')
            if not name:
                raise InputError('stop.name required')
            st_min = clock(stop.get('start'), 'stop.start')
            en_min = clock(stop.get('end'), 'stop.end')
            if en_min <= st_min:
                raise InputError(f'stop {stop.get("id", idx)} end must be after start')

            v_status = stop.get('verification_status') or ('verified' if stop.get('opening_verified') is True else 'unverified')
            icon, label, _ = _badge_info(v_status, lang)
            prefix = '' if v_status == 'verified' else f'[{label}] '
            summary = f'{prefix}{name}'

            desc_parts = [f'{icon} {label}']
            if stop.get('transit'):
                desc_parts.append(('交通：' if lang == 'zh' else 'Transit: ') + str(stop['transit']))
            elif stop.get('transfer_from_previous_minutes') is not None:
                mins = stop['transfer_from_previous_minutes']
                desc_parts.append((f'上一站衔接：约 {mins} 分钟' if lang == 'zh' else f'Transfer from previous: ~{mins} min'))
            if stop.get('cost'):
                desc_parts.append(('费用：' if lang == 'zh' else 'Cost: ') + str(stop['cost']))
            if stop.get('reservation_required'):
                confirmed = stop.get('reservation_confirmed') is True
                r_text = ('已确认预约' if confirmed else '需提前预约（未确认）') if lang == 'zh' else ('Reservation confirmed' if confirmed else 'Reservation required (unconfirmed)')
                desc_parts.append(r_text)
            if stop.get('notes'):
                desc_parts.append(str(stop['notes']))
            if stop.get('source'):
                desc_parts.append(('来源：' if lang == 'zh' else 'Source: ') + str(stop['source']))
            if stop.get('retrieved_at'):
                desc_parts.append(('核验日期：' if lang == 'zh' else 'Retrieved: ') + str(stop['retrieved_at']))

            uid = f'{day_str}-{stop.get("id", idx)}@travel-advisor-skill'
            dtstart = _fmt_dt_local(day_str, stop['start'])
            dtend = _fmt_dt_local(day_str, stop['end'])

            lines.append('BEGIN:VEVENT')
            lines.append(f'UID:{_ics_escape(uid)}')
            lines.append(f'DTSTAMP:{dtstamp}')
            if tzid:
                lines.append(f'DTSTART;TZID={_ics_escape(tzid)}:{dtstart}')
                lines.append(f'DTEND;TZID={_ics_escape(tzid)}:{dtend}')
            else:
                lines.append(f'DTSTART:{dtstart}')
                lines.append(f'DTEND:{dtend}')
            lines.append(f'SUMMARY:{_ics_escape(summary)}')
            if stop.get('address') or stop.get('location'):
                lines.append(f'LOCATION:{_ics_escape(stop.get("address") or stop.get("location"))}')
            lines.append(f'DESCRIPTION:{_ics_escape(chr(10).join(desc_parts))}')
            lines.append('END:VEVENT')
            event_count += 1

    lines.append('END:VCALENDAR')
    ics_text = '\r\n'.join(_ics_fold(line) for line in lines) + '\r\n'
    return {
        'task': 'export_ics',
        'event_count': event_count,
        'timezone': tzid or 'floating_local',
        'ics': ics_text,
    }


_CSS = """
:root { --bg:#f8fafc; --card:#ffffff; --text:#0f172a; --muted:#475569; --border:#e2e8f0;
        --ok-bg:#dcfce7; --ok-fg:#166534; --est-bg:#e0f2fe; --est-fg:#075985;
        --warn-bg:#fef3c7; --warn-fg:#92400e; --unk-bg:#f1f5f9; --unk-fg:#334155; --accent:#0f766e; }
* { box-sizing:border-box; }
body { margin:0; padding:20px 14px 40px; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Noto Sans SC",sans-serif;
       background:var(--bg); color:var(--text); line-height:1.55; }
.wrap { max-width:860px; margin:0 auto; }
header { background:var(--card); border:1px solid var(--border); border-radius:14px; padding:18px 20px; margin-bottom:16px; }
h1 { margin:0 0 6px; font-size:1.35rem; }
.meta { color:var(--muted); font-size:0.9rem; display:flex; flex-wrap:wrap; gap:8px 16px; }
.legend { margin-top:10px; font-size:0.8rem; color:var(--muted); display:flex; flex-wrap:wrap; gap:8px; }
.section { background:var(--card); border:1px solid var(--border); border-radius:14px; padding:16px 18px; margin-bottom:14px; }
.section h2 { margin:0 0 12px; font-size:1.05rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; }
.day-tag { font-size:0.8rem; color:var(--muted); font-weight:500; }
table { width:100%; border-collapse:collapse; font-size:0.9rem; }
th, td { text-align:left; padding:9px 8px; border-bottom:1px solid var(--border); vertical-align:top; }
th { color:var(--muted); font-weight:600; font-size:0.82rem; }
tr:last-child td { border-bottom:none; }
.time { white-space:nowrap; font-variant-numeric:tabular-nums; font-weight:600; color:var(--accent); }
.badge { display:inline-block; padding:1px 7px; border-radius:999px; font-size:0.75rem; font-weight:600; white-space:nowrap; }
.badge-ok { background:var(--ok-bg); color:var(--ok-fg); }
.badge-est { background:var(--est-bg); color:var(--est-fg); }
.badge-warn { background:var(--warn-bg); color:var(--warn-fg); }
.badge-unk { background:var(--unk-bg); color:var(--unk-fg); }
.plan-b { margin-top:10px; padding:9px 12px; border-radius:10px; background:#f8fafc; border-left:3px solid var(--accent); font-size:0.86rem; color:var(--muted); }
.note-list { margin:0; padding-left:18px; font-size:0.88rem; color:var(--muted); }
.sub { display:block; font-size:0.8rem; color:var(--muted); margin-top:2px; }
footer { text-align:center; color:var(--muted); font-size:0.78rem; margin-top:20px; }
@media (max-width:640px) { th, td { padding:7px 5px; font-size:0.84rem; } }
@media print { body { background:#fff; padding:0; } .section, header { break-inside:avoid; border-color:#cbd5e1; } }
""".strip()


def _e(value):
    return html.escape(str(value), quote=True)


def _render_trip_html(payload, lang):
    title = payload.get('title') or ('旅行行程单' if lang == 'zh' else 'Travel Itinerary')
    summary = payload.get('summary') or ''
    base_area = payload.get('base_area')
    party = payload.get('party')
    retrieved_at = payload.get('retrieved_at')
    days = require_list(payload.get('days'), 'days', nonempty=True)
    bookings = payload.get('booking_countdown') or []
    unknowns = payload.get('unknowns') or []

    meta_bits = []
    if party:
        meta_bits.append(('同行：' if lang == 'zh' else 'Party: ') + str(party))
    if base_area:
        meta_bits.append(('住宿锚点：' if lang == 'zh' else 'Base: ') + str(base_area))
    if retrieved_at:
        meta_bits.append(('核验基准日：' if lang == 'zh' else 'Checked on: ') + str(retrieved_at))

    parts = [
        f'<!DOCTYPE html><html lang="{"zh-CN" if lang == "zh" else "en"}"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        f'<title>{_e(title)}</title><style>{_CSS}</style></head><body><div class="wrap">',
        f'<header><h1>{_e(title)}</h1>',
    ]
    if summary:
        parts.append(f'<div style="margin-bottom:6px;font-size:0.94rem;">{_e(summary)}</div>')
    if meta_bits:
        parts.append('<div class="meta">' + ''.join(f'<span>{_e(m)}</span>' for m in meta_bits) + '</div>')

    legend = (
        '<span><span class="badge badge-ok">✅ 已核实</span> 本次实查来源</span>'
        '<span><span class="badge badge-est">≈ 估算</span> 参考区间</span>'
        '<span><span class="badge badge-warn">⚠️ 冲突/过期</span> 需复核</span>'
        '<span><span class="badge badge-unk">❓ 待核实</span> 未确认</span>'
        if lang == 'zh' else
        '<span><span class="badge badge-ok">✅ Verified</span> Live-checked</span>'
        '<span><span class="badge badge-est">≈ Estimate</span> Indicative</span>'
        '<span><span class="badge badge-warn">⚠️ Conflict/Stale</span> Recheck</span>'
        '<span><span class="badge badge-unk">❓ Unverified</span> Confirm before go</span>'
    )
    parts.append(f'<div class="legend">{legend}</div></header>')

    if bookings:
        h_book = '关键预约与购票倒计时' if lang == 'zh' else 'Booking & Ticket Countdown'
        cols = ('提前时间', '事项', '渠道 / 规则', '状态') if lang == 'zh' else ('Lead Time', 'Item', 'Channel / Rule', 'Status')
        parts.append(f'<section class="section"><h2>{_e(h_book)}</h2><table><thead><tr>'
                     + ''.join(f'<th>{c}</th>' for c in cols) + '</tr></thead><tbody>')
        for b in bookings:
            require_dict(b, 'booking_countdown item')
            icon, label, css = _badge_info(b.get('status', 'unverified'), lang)
            parts.append(
                f'<tr><td>{_e(b.get("lead_time", "—"))}</td><td><strong>{_e(b.get("item", ""))}</strong></td>'
                f'<td>{_e(b.get("channel", "—"))}</td>'
                f'<td><span class="badge {css}">{icon} {_e(label)}</span></td></tr>'
            )
        parts.append('</tbody></table></section>')

    t_cols = ('时段', '安排', '衔接', '状态与备注') if lang == 'zh' else ('Time', 'Stop / Activity', 'Transit', 'Status & Notes')
    for idx, day in enumerate(days, start=1):
        require_dict(day, 'day')
        date_value(day.get('date'), 'day.date')
        day_title = day.get('title') or (f'Day {idx} · {day["date"]}')
        pace = day.get('pace') or ''
        parts.append(f'<section class="section"><h2><span>{_e(day_title)}</span>'
                     f'<span class="day-tag">{_e(day["date"])}{(" · " + _e(pace)) if pace else ""}</span></h2>')
        parts.append('<table><thead><tr>' + ''.join(f'<th>{c}</th>' for c in t_cols) + '</tr></thead><tbody>')
        for stop in require_list(day.get('stops', []), 'day.stops'):
            require_dict(stop, 'stop')
            v_status = stop.get('verification_status') or ('verified' if stop.get('opening_verified') is True else 'unverified')
            icon, label, css = _badge_info(v_status, lang)
            time_str = f'{stop.get("start", "—")}–{stop.get("end", "—")}'
            transit = stop.get('transit') or (
                f'~{stop["transfer_from_previous_minutes"]} min' if stop.get('transfer_from_previous_minutes') is not None else '—'
            )
            note_bits = []
            if stop.get('cost'):
                note_bits.append(str(stop['cost']))
            if stop.get('notes'):
                note_bits.append(str(stop['notes']))
            if stop.get('source'):
                note_bits.append(('来源: ' if lang == 'zh' else 'Source: ') + str(stop['source']))
            sub_addr = f'<span class="sub">{_e(stop["address"])}</span>' if stop.get('address') else ''
            sub_notes = f'<span class="sub">{_e(" · ".join(note_bits))}</span>' if note_bits else ''
            parts.append(
                f'<tr><td class="time">{_e(time_str)}</td>'
                f'<td><strong>{_e(stop.get("name", ""))}</strong>{sub_addr}</td>'
                f'<td>{_e(transit)}</td>'
                f'<td><span class="badge {css}">{icon} {_e(label)}</span>{sub_notes}</td></tr>'
            )
        parts.append('</tbody></table>')
        if day.get('plan_b'):
            pb_label = '雨天 / 排队 Plan B：' if lang == 'zh' else 'Plan B (Rain / Queue): '
            parts.append(f'<div class="plan-b"><strong>{pb_label}</strong>{_e(day["plan_b"])}</div>')
        parts.append('</section>')

    if unknowns:
        h_unk = '待核实与行前确认项' if lang == 'zh' else 'Unverified & Pre-Departure Checks'
        parts.append(f'<section class="section"><h2>{_e(h_unk)}</h2><ul class="note-list">'
                     + ''.join(f'<li>{_e(u)}</li>' for u in unknowns) + '</ul></section>')

    foot = '由 Travel Advisor Skill v2.0 生成 · 价格、余票与临时闭馆请以出行前官方实时信息为准' if lang == 'zh' else 'Generated by Travel Advisor Skill v2.0 · Confirm live prices, availability, and closures via official sources before departure'
    parts.append(f'<footer>{_e(foot)}</footer></div></body></html>')
    return '\n'.join(parts)


def _render_compare_html(payload, lang):
    title = payload.get('title') or ('旅行方案对比单' if lang == 'zh' else 'Travel Option Comparison')
    bottom_line = payload.get('bottom_line') or ''
    options = require_list(payload.get('options'), 'options', nonempty=True)
    flip = payload.get('flip_conditions') or []

    parts = [
        f'<!DOCTYPE html><html lang="{"zh-CN" if lang == "zh" else "en"}"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        f'<title>{_e(title)}</title><style>{_CSS}</style></head><body><div class="wrap">',
        f'<header><h1>{_e(title)}</h1>',
    ]
    if bottom_line:
        parts.append(f'<div style="font-size:0.95rem;">{_e(bottom_line)}</div>')
    parts.append('</header>')

    cols = ('选项', '同口径总价', '条件与状态', '优缺点 / 备注') if lang == 'zh' else ('Option', 'All-in Total', 'Terms & Status', 'Trade-offs / Notes')
    parts.append('<section class="section"><table><thead><tr>' + ''.join(f'<th>{c}</th>' for c in cols) + '</tr></thead><tbody>')
    for opt in options:
        require_dict(opt, 'option')
        icon, label, css = _badge_info(opt.get('evidence_status', 'unverified'), lang)
        price_text = f'{opt["all_in_price"]:.2f} {opt.get("currency") or ""}'.strip() if opt.get('all_in_price') is not None else ('待核实' if lang == 'zh' else 'Unverified')
        if opt.get('fx_converted') and opt.get('original_price') is not None:
            price_text += f' ({opt["original_price"]:.2f} {opt.get("original_currency") or ""})'
        notes = opt.get('notes') or ', '.join(opt.get('issues') or []) or '—'
        parts.append(
            f'<tr><td><strong>{_e(opt.get("name", opt.get("id", "")))}</strong></td>'
            f'<td class="time">{_e(price_text)}</td>'
            f'<td><span class="badge {css}">{icon} {_e(label)}</span></td>'
            f'<td>{_e(notes)}</td></tr>'
        )
    parts.append('</tbody></table></section>')

    if flip:
        h_flip = '怎么拍板（翻转条件）' if lang == 'zh' else 'How to Decide (Flip Conditions)'
        parts.append(f'<section class="section"><h2>{_e(h_flip)}</h2><ul class="note-list">'
                     + ''.join(f'<li>{_e(f)}</li>' for f in flip) + '</ul></section>')

    foot = '由 Travel Advisor Skill v2.0 生成 · 仅同条件报价参与价格排序' if lang == 'zh' else 'Generated by Travel Advisor Skill v2.0 · Only equivalent packages share a price ranking'
    parts.append(f'<footer>{_e(foot)}</footer></div></body></html>')
    return '\n'.join(parts)


def export_html(payload, lang='auto'):
    """Export either an itinerary ('trip') or comparison ('compare') to single-file offline HTML."""
    require_dict(payload)
    lang = detect_lang(payload, lang)
    kind = payload.get('export_kind') or ('compare' if 'options' in payload and 'days' not in payload else 'trip')
    if kind not in ('trip', 'compare'):
        raise InputError('export_kind must be trip or compare')
    document = _render_trip_html(payload, lang) if kind == 'trip' else _render_compare_html(payload, lang)
    return {
        'task': 'export_html',
        'export_kind': kind,
        'lang': lang,
        'html': document,
    }
