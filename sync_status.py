#!/usr/bin/env python3
"""Meta status generator for the cron dashboard (accounts 71 & 72).

Runs ON THE VPS where the Meta token lives. Reads CAMPAIGN_IDS straight from the
toggle scripts (so it can never drift), does ONE Graph batch read per account,
and writes data/a71.json + data/a72.json with NON-SECRET status only
(name, ON/OFF, budget, objective). The token never appears in the output.

Usage:  python3 sync_status.py            # write JSON files
        python3 sync_status.py --print    # also print a short summary
No secrets are printed/logged.
"""
from __future__ import annotations
import json, os, re, sys, warnings
from datetime import datetime, timezone, timedelta
from pathlib import Path
warnings.filterwarnings('ignore')
import requests

AUTODIR = Path('/root/automation')
OUTDIR = Path(__file__).resolve().parent / 'data'
GRAPH = 'https://graph.facebook.com/v23.0/'
ENV_FILE = AUTODIR / '.a71_videos.env'
WIB = timezone(timedelta(hours=7))

# account -> (act_id, list of toggle scripts whose CAMPAIGN_IDS belong to it)
ACCT = {
    'a71': ('1128908469237968', ['a71_videos_6_26_toggle.py', 'a71_batch_6_26_toggle.py']),
    'a72': ('8682526015207885', ['a72_statue_toggle.py']),
}


def load_token() -> str:
    for line in ENV_FILE.read_text(errors='ignore').splitlines():
        s = line.strip()
        if s and not s.startswith('#') and '=' in s:
            k, v = s.split('=', 1)
            if 'TOKEN' in k.upper() or 'ACCESS' in k.upper():
                return v.strip().strip('"').strip("'")
    raise SystemExit('no meta token in env')


def parse_ids(script: str) -> list[tuple[str, str]]:
    """Return [(campaign_id, label)] from the ACTIVE CAMPAIGN_IDS block only."""
    txt = (AUTODIR / script).read_text(errors='ignore')
    m = re.search(r'CAMPAIGN_IDS\s*=\s*\[(.*?)\]', txt, re.S)
    if not m:
        return []
    out = []
    for line in m.group(1).splitlines():
        s = line.strip()
        if s.startswith('#'):
            continue
        cid = re.match(r'["\'](\d{15,})["\']', s)
        if not cid:
            continue
        note = ''
        c = s.split('#', 1)
        if len(c) > 1:
            note = c[1].strip()
        out.append((cid.group(1), note))
    return out


def graph_batch(token: str, ids: list[str]) -> dict:
    if not ids:
        return {}
    r = requests.get(GRAPH, params={
        'ids': ','.join(ids),
        'fields': 'name,effective_status,daily_budget,lifetime_budget,objective',
        'access_token': token,
    }, timeout=90)
    return r.json() if r.status_code == 200 else {'__error__': r.status_code}


def fmt_budget(c: dict) -> str:
    raw = c.get('daily_budget') or c.get('lifetime_budget')
    if not raw:
        return '-'
    try:
        # IDR on Meta Graph is already rupiah units. Do NOT divide by 100:
        # daily_budget=100000 means Rp100.000/day, not Rp1.000/day.
        rp = int(raw)
        kind = 'hari' if c.get('daily_budget') else 'total'
        return f'Rp{rp:,.0f}/{kind}'.replace(',', '.')
    except Exception:
        return '-'


def main():
    show = '--print' in sys.argv
    token = load_token()
    now = datetime.now(WIB).strftime('%Y-%m-%d %H:%M:%S WIB')
    OUTDIR.mkdir(parents=True, exist_ok=True)

    for acct, (act_id, scripts) in ACCT.items():
        pairs = []
        for sc in scripts:
            pairs += parse_ids(sc)
        ids = [c for c, _ in pairs]
        label = {c: n for c, n in pairs}
        data = graph_batch(token, ids)
        err = data.get('__error__')
        camps = []
        on = off = unknown = 0
        for cid in ids:
            obj = data.get(cid) if isinstance(data, dict) else None
            if not obj or 'effective_status' not in obj:
                unknown += 1
                camps.append({'id': cid, 'name': label.get(cid, cid),
                              'on': None, 'status': 'UNKNOWN', 'budget': '-', 'objective': '-'})
                continue
            es = obj.get('effective_status', '')
            is_on = es == 'ACTIVE'
            on += 1 if is_on else 0
            off += 0 if is_on else 1
            camps.append({
                'id': cid,
                'name': obj.get('name') or label.get(cid, cid),
                'on': is_on,
                'status': es,
                'budget': fmt_budget(obj),
                'objective': obj.get('objective', '-'),
            })
        out = {
            'account': acct, 'act_id': act_id,
            'synced_at': now,
            'total': len(ids), 'on': on, 'off': off, 'unknown': unknown,
            'error': err,
            'campaigns': camps,
        }
        (OUTDIR / f'{acct}.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
        if show:
            print(f'{acct}: total={len(ids)} on={on} off={off} unknown={unknown} err={err}')


if __name__ == '__main__':
    main()
