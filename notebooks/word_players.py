"""Which players a word attaches to: for every common word, the share of each
player's sentences (Fox's, and the five sports outlets') that contain it.
Writes static/data/word_players.json, fetched by the {.WordPlayers} chart.

    python3 notebooks/word_players.py
"""
import csv, json, re
from collections import Counter, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
csv.field_size_limit(10 ** 9)
FROM, MIN_WORD = "2023-04-01", 30
STOP = set("""a an the and or but of in on at to for with by from as is are was were be been being it its
this that these those i you he she they we his her their our your my not no do does did has have had
will would can could should may might must about after before over under again more most other some
such only own same so too very what which who whom when where why how all any both each few said says
say new just also even still back one two""".split())
totals = defaultdict(lambda: [0, 0])                 # player -> [fox sentences, others sentences]
hits = defaultdict(lambda: defaultdict(lambda: [0, 0]))  # word -> player -> [fox, others]
for r in csv.DictReader((HERE / "data" / "player_sentences.csv").open()):
    if r["date"] < FROM: continue
    side = 0 if r["outlet"] == "Fox News" else 1
    totals[r["player"]][side] += 1
    words = set(re.findall(r"[a-z][a-z'-]*[a-z]", r["sentence"].lower().replace("’", "'")))
    for w in words:
        if w in STOP or len(w) < 3: continue
        hits[w][r["player"]][side] += 1
out = {"totals": dict(totals), "words": {}}
for w, byp in hits.items():
    if sum(a + b for a, b in byp.values()) < MIN_WORD: continue
    out["words"][w] = {p: v for p, v in byp.items()}
OUT = HERE / "static" / "data" / "word_players.json"
OUT.write_text(json.dumps(out, separators=(",", ":")))
print(f"{len(out['words'])} words · {len(totals)} players · {OUT.stat().st_size / 1e6:.1f} MB")
d = out["words"].get("dirty", {}); print("dirty:", sorted(((p, v) for p, v in d.items()), key=lambda t: -t[1][0])[:6])
