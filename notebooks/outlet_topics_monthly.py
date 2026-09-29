"""Monthly topic counts per outlet (the yearly ones are notebook 05's
outlet_topics.csv), for the small multiples
"""
import csv, re, sys
from collections import Counter, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "notebooks"))
from outlets import OUTLETS
import topics
csv.field_size_limit(10 ** 9)
pats = topics.patterns()
PATTERNS = {"polrace": re.compile(pats["politics or race"], re.I),
            "lgbtq": re.compile(pats["LGBTQ or trans"], re.I),
            "fouls": re.compile(pats["fouls"], re.I),
            "protect": re.compile(pats["protect"], re.I)}
PAIRS = [("fouls", "protect"), ("polrace", "lgbtq")]
records = []
for key, label, *_ in OUTLETS:
    months = {t: defaultdict(Counter) for t in list(PATTERNS) + [f"{a}&{b}" for a, b in PAIRS]}
    for r in csv.DictReader((HERE / "data" / f"{key}.csv").open()):
        d, body = (r.get("date") or "")[:7], r.get("body") or ""
        if len(d) < 7 or d < "2019-01" or len(body.split()) <= 80:
            continue
        text = (r.get("headline") or "") + " " + body
        hits = {}
        for t, rx in PATTERNS.items():
            months[t][d]["n"] += 1
            hits[t] = bool(rx.search(text))
            if hits[t]:
                months[t][d]["hit"] += 1
        # the overlap of two topics, for a stack that splits them without
        # double counting ("fouls&protect": articles with both)
        for a, b in PAIRS:
            months[f"{a}&{b}"][d]["n"] += 1
            if hits[a] and hits[b]:
                months[f"{a}&{b}"][d]["hit"] += 1
    for t in months:
        for m, v in sorted(months[t].items()):
            records.append((t, "body", label, m, v["n"], v["hit"]))
out = HERE / "src/data/outlet_topics_monthly.csv"
with out.open("w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["topic", "method", "outlet", "period", "articles", "hits"]); w.writerows(records)
print(f"{len(records)} rows -> {out.name}")
