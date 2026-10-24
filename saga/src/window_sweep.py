import json, collections
rows = []
for W, p in [(1, 'results/window_sweep_W1'), (3, 'results'), (6, 'results/window_sweep_W6'), (12, 'results/window_sweep_W12')]:
    R = [json.loads(l) for l in open(p + '/runs.jsonl')]
    R = [r for r in R if r['framework'] == 'langgraph']
    lab = {json.loads(l)['op']: json.loads(l)['label'] for l in open(p + '/operation_labels.jsonl')}
    for order in ['original', 'irreversible_last']:
        rs = [r for r in R if r['recovery'] == 'effect_log' and r['order'] == order and r['effect_steps']]
        c = collections.Counter(r['outcome'] for r in rs)
        wc = sum(1 for r in rs for x in r['compensation'] if x['result'] == 'window_closed')
        rows.append(f"| {W} | {lab['email_send']} | {order} | {len(rs)} | {c['clean']} | {c['residue']} | {c['stuck']} | {wc} |")
out = "# Window sensitivity (LangGraph runs, effect-log saga recovery, non-trivial runs)\n\n| Window (ticks) | email_send label | Order | n | clean | residue | stuck | window-closed inverses |\n|---|---|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n"
open('results/window_sweep.md', 'w').write(out); print(out)
