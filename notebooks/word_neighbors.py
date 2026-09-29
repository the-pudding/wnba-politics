"""The words that sit next to a word: the neighbours chart ({.WordNeighbors}).
For every reasonably common word, the words that appear immediately before
or after it (the two pooled), counted in Fox's articles and in the five
sports outlets' (April 2023 on, full text), with one example sentence per
corpus. Each neighbour carries a raw count and a weighted score: how much
more often it sits next to the word than its overall frequency would give
(the pointwise-mutual-information idea the Pudding's chyron chart used).
The chart shows the two corpora as side-by-side columns. Names are kept whole ("caitlin clark" is one token).
Writes static/data/word_neighbors.json, fetched by the chart on first use
(it is a few MB, so it is served as a plain file rather than bundled).

    python3 notebooks/word_neighbors.py
"""
import csv, json, re
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
csv.field_size_limit(10 ** 9)
FROM = "2023-04-01"
MIN_WORD = 40          # a word needs this many uses in one corpus to be searchable
KEEP = 20              # neighbours kept per corpus, by each measure
MIN_PAIR = 4           # a neighbour needs this many co-occurrences to be weighted
STOP = set("""a an the and or but of in on at to for with by from as is are was were be been being
it its this that these those his her their our your my he she they we you i them him us me who
which what where when while than then there here has have had do does did will would can could
should may might must said says say also just very more most much many some any all each both
into over under about after before through during out up down off so if because until""".split())
BOILER = re.compile(r"click here[^.]*\.|get the fox news app|fox news digital|follow (?:us|fox news digital)[^.]*\.|"
                    r"sign up[^.]*newsletter[^.]*\.|download the [^.]*app[^.]*\.|contributed to this report\.?|"
                    r"all rights reserved|&nbsp;|&amp;|&quot;|&#\d+;", re.I)
people = json.loads((HERE / "src" / "data" / "people.json").read_text())
NAMES = sorted((n for n in people), key=len, reverse=True)
NAME_RX = [(re.compile(r"\b" + re.escape(n.lower().replace("’", "'")) + r"\b"), n.lower().replace(" ", "_").replace("'", "")) for n in NAMES]
SHOW = {n.lower().replace(" ", "_").replace("'", ""): n for n in NAMES}

def tokens(text):
    t = BOILER.sub(" ", text).lower().replace("’", "'")
    for rx, tok in NAME_RX:
        t = rx.sub(tok, t)
    # a name's possessive is the name ("Chennedy Carter's foul" -> the name)
    t = re.sub(r"(\w+_\w+)'s\b", r"\1", t)
    return re.findall(r"[a-z][a-z'_-]*[a-z]|[a-z]", t)

def sentences(text):
    return re.split(r"(?<=[.!?])\s+", BOILER.sub(" ", " ".join(text.split())))

def load(files):
    docs = []
    for f in files:
        for r in csv.DictReader((HERE / "data" / f).open()):
            if r["date"] < FROM: continue
            body = r.get("body") or ""
            if len(body.split()) < 80: continue
            docs.append((r["headline"] or "") + ". " + body)
    return docs

def neighbours(docs):
    total, near, eg = Counter(), defaultdict(Counter), {}
    for d in docs:
        for s in sentences(d):
            ts = tokens(s)
            for i, w in enumerate(ts):
                total[w] += 1
                if i and ts[i - 1] not in STOP: near[w][ts[i - 1]] += 1
                if i + 1 < len(ts) and ts[i + 1] not in STOP: near[w][ts[i + 1]] += 1
                if w not in eg and 40 <= len(s) <= 180: eg[w] = s.strip()
    return total, near, eg, sum(total.values())

fox = neighbours(load(["fox_wnba.csv"]))
import sys as _sys; _sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
from outlets import FILES as OUTLET_FILES, SPORTS, NEWS, COMPARISON, GROUPS as OUTLET_GROUPS, OUTLETS as OUTLET_TABLE
oth = neighbours(load([OUTLET_FILES[label] for label in COMPARISON]))
out = {"words": {}, "show": {}}
for w in set(fox[0]) | set(oth[0]):
    if w in STOP or len(w) < 3: continue
    if fox[0][w] < MIN_WORD and oth[0][w] < MIN_WORD: continue
    entry = {}
    for key, (total, near, eg, N) in (("fox", fox), ("others", oth)):
        pairs = near[w]
        # the lift, damped for thin pairs so a word seen four times next to
        # this one cannot outrank one seen forty times
        weighted = {v: (n / max(1, total[w])) / (total[v] / N) * (n / (n + 6))
                    for v, n in pairs.items() if n >= MIN_PAIR and total[v]}
        keep = {v for v, _ in pairs.most_common(KEEP)} | {v for v, _ in sorted(weighted.items(), key=lambda kv: -kv[1])[:KEEP]}
        entry[key] = {"n": total[w],
                      "near": sorted(([v, pairs[v], round(weighted.get(v, 0), 2)] for v in keep), key=lambda t: -t[1]),
                      "eg": eg.get(w, "")}
    out["words"][w] = entry
for tok, name in SHOW.items():
    if tok in out["words"]: out["show"][tok] = name
OUT = HERE / "static" / "data" / "word_neighbors.json"
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(json.dumps(out, separators=(",", ":")))
print(f"{len(out['words'])} searchable words · {OUT.stat().st_size / 1e6:.1f} MB")
for w in ("foul", "white", "protect"):
    e = out["words"].get(w)
    if e:
        print(w, "| fox raw:", [t[0] for t in e["fox"]["near"][:6]], "| fox weighted:", [t[0] for t in sorted(e["fox"]["near"], key=lambda t: -t[2])[:6]])
