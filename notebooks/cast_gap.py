"""The cast around the league in the dot plot: Trump, Portnoy, Wallen and the
rest, Fox News against the sports press.

The dot plot's recipe (05-outlet-topics.ipynb) for the roster's non-players,
matched with each person's pattern from src/data/people.json, over the window
every outlet covers. Each person's share of an outlet's WNBA headlines, Fox
against the pooled sports press, gives the k× figure. Writes
src/data/cast_gap.json in the dot plot's shape, with an example Fox headline.

    python3 notebooks/cast_gap.py
"""
import csv, json, re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
csv.field_size_limit(10 ** 9)
MIN_HEADLINES = 1
GAP_FILES = {"Yahoo Sports": "yahoo_sports.csv", "ESPN": "espn.csv", "CBS Sports": "cbs_sports.csv",
             "USA Today": "usa_today.csv", "The Athletic": "the_athletic.csv",
             "Just Women's Sports": "just_womens_sports.csv"}
GROUPS = {"Yahoo + ESPN": ["Yahoo Sports", "ESPN"], "CBS + USA Today": ["CBS Sports", "USA Today"]}
# Obama is Barack unless Michelle is named; Biden is Joe unless Jill is
NOT_THEM = {"Barack Obama": r"michelle obama", "Joe Biden": r"jill biden"}

roster = json.load(open(ROOT / "src/data/people.json"))
cast = {name: p for name, p in roster.items() if p.get("group") != "players" and p.get("rx")}
rx = {name: re.compile(p["rx"], re.I) for name, p in cast.items()}
not_rx = {n: re.compile(r, re.I) for n, r in NOT_THEM.items()}

def names_in(text):
    out = []
    for name, r in rx.items():
        if not r.search(text):
            continue
        guard = not_rx.get(name)
        if guard and guard.search(text) and not re.search(re.escape(name.split()[0]), text, re.I):
            continue
        out.append(name)
    return out

rows_by_outlet = defaultdict(list)
seen = set()
for row in csv.DictReader(open(ROOT / "data/fox_wnba.csv")):
    h, d = (row["headline"] or "").strip(), (row["date"] or "")[:10]
    if h and d and h not in seen:
        seen.add(h); rows_by_outlet["Fox News"].append((d, h))
for outlet, f in GAP_FILES.items():
    for row in csv.DictReader(open(ROOT / "data" / f)):
        h, d = (row["headline"] or "").strip(), (row["date"] or "")[:10]
        if h and d:
            rows_by_outlet[outlet].append((d, h))
compared = ["Fox News"] + sorted(GAP_FILES)
window = (max(min(d for d, _ in rows_by_outlet[o]) for o in compared),
          min(max(d for d, _ in rows_by_outlet[o]) for o in compared))

totals, hits, example = Counter(), defaultdict(Counter), {}
for outlet, entries in rows_by_outlet.items():
    for d, h in entries:
        if not (window[0] <= d <= window[1]):
            continue
        totals[outlet] += 1
        for name in names_in(h):
            hits[outlet][name] += 1
            if outlet == "Fox News":
                example.setdefault(name, {"date": d, "headline": h})

baseline = sorted(GAP_FILES)
baseline_total = sum(totals[o] for o in baseline)
rows = []
for name, p in cast.items():
    fox_n = hits["Fox News"][name]
    base_n = sum(hits[o][name] for o in baseline)
    if fox_n + base_n < MIN_HEADLINES:
        continue
    fox_share, base_share = fox_n / totals["Fox News"], base_n / baseline_total
    rows.append({
        "name": name, "group": p.get("group"),
        "fox": round(fox_share, 5), "foxN": fox_n, "sports": round(base_share, 5), "sportsN": base_n,
        "byOutlet": {
            **{o: {"share": round(hits[o][name] / totals[o], 5), "n": hits[o][name]} for o in baseline if totals[o]},
            **{label: {"share": round(sum(hits[o][name] for o in outlets) / max(1, sum(totals[o] for o in outlets)), 5),
                       "n": sum(hits[o][name] for o in outlets)} for label, outlets in GROUPS.items()},
        },
        "ratio": round(fox_share / base_share, 2) if base_share else None,
        "ex": example.get(name), "news": {},
    })
rows.sort(key=lambda r: -r["foxN"])
out = {"groups": GROUPS, "window": {"from": window[0], "to": window[1]},
       "totals": {o: totals[o] for o in totals if totals[o] >= 100}, "baseline": baseline, "people": rows}
(ROOT / "src/data/cast_gap.json").write_text(json.dumps(out))
print(f"{len(rows)} cast members over {window[0]}..{window[1]}")
five = ["ESPN", "CBS Sports", "USA Today", "The Athletic", "Just Women's Sports"]
ft = sum(totals[o] for o in five)
for r in rows:
    pn = sum(r["byOutlet"][o]["n"] for o in five if o in r["byOutlet"])
    k = (r["fox"] / (pn / ft)) if pn else None
    print(f"  {r['name']:20} {r['group']:9} Fox {r['foxN']:3}  five {pn:4}  {'Fox only' if k is None else f'{k:5.1f}x'}")
