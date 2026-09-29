"""Pairs of players in the same headline: Fox News against the sports press.

The dot plot's recipe (05-outlet-topics.ipynb) applied to pairs. A headline
counts for a pair when it names both players (by surname, minus the
look-alikes), over the window every outlet covers. Each pair's share of an
outlet's headlines, Fox against the pooled sports press, gives the k× figure.
Writes src/data/pair_gap.json in the dot plot's shape, with `names` for the
two faces and an example Fox headline.

    python3 notebooks/pair_gap.py
"""
import csv, json, re
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
csv.field_size_limit(10 ** 9)
MIN_FOX_HEADLINES = 3          # a player needs this many Fox headlines to be in the pool
MIN_PAIR = 3                   # a pair needs this many headlines somewhere to be shown
import sys as _sys; _sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from outlets import FILES as OUTLET_FILES, SPORTS, NEWS, COMPARISON, GROUPS as OUTLET_GROUPS, OUTLETS as OUTLET_TABLE
GAP_FILES = {label: OUTLET_FILES[label] for label in COMPARISON}
GROUPS = dict(OUTLET_GROUPS)                     # every pool with members (the registry decides)
NOT_HER = {"Sue Bird": r"larry bird|bird-magic|bird and magic",
           "A'ja Wilson": r"russell wilson|signs with wilson|wilson (?:basketball|ball|brand)",
           "Alyssa Thomas": r"lia thomas|isiah thomas", "Caitlin Clark": r"alysha clark"}
NOT_HER_RX = {n: re.compile(rx, re.I) for n, rx in NOT_HER.items()}

DOT_PLOT_PLAYERS = [   # hand-picked: the chart's cast, in this order
    "Caitlin Clark", "Angel Reese", "Brittney Griner", "Sophie Cunningham", "Paige Bueckers",
    "Sue Bird", "DiJonai Carrington", "A'ja Wilson", "Sabrina Ionescu", "Aliyah Boston",
    "Breanna Stewart", "Alyssa Thomas", "Diana Taurasi", "Kelsey Plum", "Cameron Brink",
    "Candace Parker", "Natasha Cloud", "Napheesa Collier", "Chennedy Carter",
    "Nneka Ogwumike", "Kelsey Mitchell",
]
roster = json.load(open(ROOT / "src/data/people.json"))
players = list(DOT_PLOT_PLAYERS)
name_rx = {n: re.compile(r"\b(?:" + roster[n]["rx"] + r")\b", re.I) for n in players}

def names_in(text):
    found = []
    for name, rx in name_rx.items():
        if not rx.search(text):
            continue
        guard = NOT_HER_RX.get(name)
        if guard and guard.search(text) and not re.search(re.escape(name.split()[0]), text, re.I):
            continue
        found.append(name)
    return found

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
# the shared window is anchored on the original five sports outlets; the news
# arms run shorter and would clip it for everyone
compared = ["Fox News"] + list(COMPARISON)   # the registry's comparison outlets
window = (max(min(d for d, _ in rows_by_outlet[o]) for o in compared),
          min(max(d for d, _ in rows_by_outlet[o]) for o in compared))

totals, hits, example = Counter(), defaultdict(Counter), {}
for outlet, entries in rows_by_outlet.items():
    for d, h in entries:
        if not (window[0] <= d <= window[1]):
            continue
        totals[outlet] += 1
        named = sorted(set(names_in(h)))
        for pair in combinations(named, 2):
            hits[outlet][pair] += 1
            if outlet == "Fox News":
                example.setdefault(pair, {"date": d, "headline": h})

baseline = list(SPORTS) or list(COMPARISON)   # "the sports press" when there is one, else everyone pooled
baseline_total = sum(totals[o] for o in baseline)
pairs = set()
for outlet in hits:
    pairs |= set(hits[outlet])
rows = []
for pair in pairs:
    fox_n = hits["Fox News"][pair]
    base_n = sum(hits[o][pair] for o in baseline)
    if fox_n + base_n < MIN_PAIR:
        continue
    fox_share, base_share = fox_n / totals["Fox News"], base_n / baseline_total
    rows.append({
        "name": " + ".join(pair), "names": list(pair),
        "fox": round(fox_share, 5), "foxN": fox_n, "sports": round(base_share, 5), "sportsN": base_n,
        "byOutlet": {
            **{o: {"share": round(hits[o][pair] / totals[o], 5), "n": hits[o][pair]} for o in baseline if totals[o]},
            **{label: {"share": round(sum(hits[o][pair] for o in outlets) / max(1, sum(totals[o] for o in outlets)), 5),
                       "n": sum(hits[o][pair] for o in outlets)} for label, outlets in GROUPS.items()},
        },
        "ratio": round(fox_share / base_share, 2) if base_share else None,
        "ex": example.get(pair), "news": {},
    })
rows.sort(key=lambda r: -r["foxN"])
out = {"groups": GROUPS, "window": {"from": window[0], "to": window[1]},
       "totals": {o: totals[o] for o in totals if totals[o] >= 100}, "baseline": baseline, "people": rows}
(ROOT / "src/data/pair_gap.json").write_text(json.dumps(out))
print(f"{len(rows)} pairs over {window[0]}..{window[1]}; players in pool: {len(players)}")
for r in rows[:15]:
    k = r["fox"] / r["sports"] if r["sports"] else float("inf")
    print(f"  {r['name']:38} Fox {r['foxN']:3}  press {r['sportsN']:4}  {k:5.1f}x  {r['ex']['headline'][:70] if r['ex'] else ''}")
