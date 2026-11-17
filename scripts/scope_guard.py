#!/usr/bin/env python3
"""Check proposed outputs/operations against an explicitly supplied task scope.

Does NOT classify natural-language intent. Useful as a regression/CI safety check.
Input JSON: {"scope": "compare", "proposed_outputs": ["comparison"],
             "proposed_operations": ["research", "normalize", "evaluate"]}
"""
import json
import sys
from pathlib import Path

POLICIES = {
    'discover': ({'shortlist'}, {'research', 'normalize', 'evaluate', 'validate'}),
    'verify': ({'fact_check'}, {'research', 'normalize', 'validate'}),
    'compare': ({'comparison'}, {'research', 'normalize', 'evaluate', 'validate', 'budget'}),
    'budget': ({'budget_scenarios'}, {'research', 'normalize', 'budget', 'evaluate', 'validate'}),
    'plan': ({'itinerary', 'comparison', 'budget_scenarios'}, {'research', 'normalize', 'budget', 'schedule', 'evaluate', 'validate'}),
    'audit': ({'audit_report'}, {'research', 'normalize', 'budget', 'validate'}),
    'revise': ({'change_summary'}, {'research', 'normalize', 'budget', 'schedule', 'validate', 'evaluate', 'revise'}),
}
DANGEROUS = {'book', 'pay', 'cancel', 'share_private', 'persistent_tracking'}


def check_scope(payload):
    if not isinstance(payload, dict):
        raise ValueError('object required')
    scope = payload.get('scope')
    if scope not in POLICIES:
        raise ValueError('unknown scope')
    outs = payload.get('proposed_outputs', [])
    ops = payload.get('proposed_operations', [])
    if not isinstance(outs, list) or not outs or not all(isinstance(x, str) for x in outs):
        raise ValueError('nonempty output list required')
    if not isinstance(ops, list) or not all(isinstance(x, str) for x in ops):
        raise ValueError('operation list required')
    output_allow, operation_allow = POLICIES[scope]
    rejected = {
        'outputs': sorted(set(outs) - output_allow),
        'operations': sorted(set(ops) - operation_allow),
    }
    forbidden = sorted(set(ops) & DANGEROUS)
    return {'scope': scope, 'within_scope': not any(rejected.values()), 'rejected': rejected,
            'sensitive_operations_not_permitted': forbidden,
            'note': 'Explicit scope guard only; decisions and provider permissions require runtime checks.'}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python scripts/scope_guard.py examples/scope_demo.json')
    print(json.dumps(check_scope(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))), ensure_ascii=False, indent=2))
