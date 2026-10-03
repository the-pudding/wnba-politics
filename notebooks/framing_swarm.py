"""Data for the explore beeswarm and its headline table
(static/data/framing_swarm.json, used by FramingSwarm.svelte).

Reads the framing measures (notebook 01, sentence_framing.py) and the headline
files; run after those:

    python notebooks/framing_swarm.py
"""
import csv, json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
D = HERE / "src/data"
OUT = HERE / "static/data/framing_swarm.json"

# ---------------------------------------------------------------------------
# Edit these
# ---------------------------------------------------------------------------

# the measures, in tab order after Tone
MEASURES = ["political", "appearance", "celebrity", "performance"]
# a player is on the chart, counting by headline, with at least this many
# headlines naming her (by sentence, sentence_framing.json sets its own minimum)
MIN_HEADLINES = 10

# ---------------------------------------------------------------------------

roster = json.loads((D / "people.json").read_text())
is_player = lambda n: roster.get(n, {}).get("group") == "players"
names_in = lambda s: s.split("; ") if s else []

# by sentence: ready-made per person
sf = json.loads((D / "sentence_framing.json").read_text())
by_sentence = {}
for name, p in sf["people"].items():
    if not is_player(name):
        continue
    by_sentence[name] = {
        "n": p["count"], "tone": p["tone"],
        **{m: p[m] for m in MEASURES},
        **{m + "N": p[m + "N"] for m in MEASURES},
        "ex": {m: p.get(m + "Example") or "" for m in MEASURES},
        "worst": p["worst"], "best": p["best"],
    }

# the headlines, once each
sentiment = list(csv.DictReader((D / "headline_sentiment.csv").open()))
score = {r["headline"]: float(r["score"]) for r in sentiment}
label = {r["headline"]: r["label"] for r in sentiment}
# a headline's topics; looks, celebrity and play name whom the words are about
# (notebook 01 works that out from the grammar), politics doesn't
tags = {r["headline"]: {m: ([] if m == "political" else r[m].split("; ")) for m in MEASURES if r[m]}
        for r in csv.DictReader((D / "labeled_headlines.csv").open())}
seen, rows = set(), []
for r in csv.DictReader((D / "fox_player_headlines.csv").open()):
    if (r["date"], r["title"]) not in seen:
        seen.add((r["date"], r["title"]))
        rows.append(r)

# by headline: tone is the mean score of the headlines naming her; the shares
# come from framing.csv
scored = defaultdict(list)
for r in rows:
    if r["title"] in score:
        for n in names_in(r["players"]):
            if is_player(n):
                scored[n].append((score[r["title"]], r["title"]))
framing = defaultdict(dict)
METRIC = {"politicization": "political", "appearance": "appearance", "celebrity": "celebrity", "performance": "performance"}
for r in csv.DictReader((D / "framing.csv").open()):
    m = METRIC.get(r["metric"])
    if m and r["name"] not in framing[m]:
        framing[m][r["name"]] = r
by_headline = {}
for name, s in scored.items():
    if len(s) < MIN_HEADLINES:
        continue
    s.sort()
    rec = {"n": len(s), "tone": round(sum(x for x, _ in s) / len(s), 4), "worst": s[0][1], "best": s[-1][1], "ex": {}}
    for m in MEASURES:
        f = framing[m].get(name)
        rec[m] = float(f["share"]) if f else 0.0
        rec[m + "N"] = int(float(f["political" if m == "political" else "hits"] or 0)) if f else 0
        rec["ex"][m] = (f["example"] if m == "political" else f["example_title"]) if f else ""
    by_headline[name] = rec

# the players on the chart (faces are in static/net)
players = [{"name": n, "face": roster[n].get("face"), "s": by_sentence.get(n), "h": by_headline.get(n)}
           for n in sorted(set(by_sentence) | set(by_headline), key=lambda n: n.split(" ")[-1])]

# the table: every headline, with names as indexes into one list
everyone = sorted({n for r in rows for n in names_in(r["players"])}
                  | {n for t in tags.values() for ns in t.values() for n in ns})
idx = {n: i for i, n in enumerate(everyone)}
table = [[r["date"], r["title"], r["url"], [idx[n] for n in names_in(r["players"])],
          [[MEASURES.index(m), [idx[n] for n in ns]] for m, ns in tags.get(r["title"], {}).items()],
          score.get(r["title"]), label.get(r["title"], "")]
         for r in rows]

OUT.write_text(json.dumps({
    "minSentences": sf["minSentences"], "minHeadlines": MIN_HEADLINES,
    "measures": MEASURES, "players": players, "names": everyone, "headlines": table,
    "window": [min(r["date"] for r in rows), max(r["date"] for r in rows)],
}, ensure_ascii=False, separators=(",", ":")))
print(f"{len(players)} players ({len(by_sentence)} by sentence, {len(by_headline)} by headline), {len(table)} headlines")
