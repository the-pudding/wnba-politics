"""Two-word phrases in the sentences about each player, Fox News against the
five sports outlets: the "phrases" tab of the player-words chart. Same
fightin'-words scoring as the rest. Names and teams are dropped without a
list: a phrase that is capitalised in most of its raw occurrences is a proper
noun. Writes src/data/player_phrases.json in the player-words shape.

    python3 notebooks/player_phrases.py
"""
import csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "notebooks"))
from fighting_words import bayes_compare_language
from sklearn.feature_extraction.text import CountVectorizer as CV
csv.field_size_limit(10 ** 9)
FROM, MIN_SENTENCES, MIN_PAIR, TOP = "2023-04-01", 150, 5, 40
STOP = set("""a an the and or but of in on at to for with by from as is are was were be been being it its
this that these those i you he she they we his her their our your my not no do does did has have had
will would can could should may might must about after before over under again more most other some
such only own same so too very what which who whom when where why how all any both each few said says
say new just also even still back one two her's she's it's
first second last""".split())   # first/second/last: game-time ordinals, not framing (2026-09-30)
BAD = re.compile(r"\b(?:contributed report|click here|view post|instagram post|post instagram|getty images|"
                 r"associated press|fox news|fox sports|news digital|read more|foxnews com|usa today)\b")
# names and teams, belt and braces: any part of a roster name (unless it is
# an ordinary word), the league's cities and nicknames, and anything the
# capitalisation test catches
COMMON = {"white", "cloud", "freedom", "bird", "young", "plum", "gray", "hill", "swift", "silver", "brink", "hull", "bout", "rice", "miles"}
people = json.loads((HERE / "src" / "data" / "people.json").read_text())
NAME_PARTS = {re.sub(r"[^a-z]", "", part.lower()) for name in people for part in name.split()
              if len(part) > 2 and part.lower() not in COMMON}
NAME_PARTS |= set("""fever sky liberty aces lynx storm mercury dream sun wings sparks mystics valkyries tempo fire
indiana chicago york vegas minnesota seattle phoenix atlanta connecticut dallas angeles washington golden
toronto portland iowa hawkeyes lsu tigers uconn huskies usc trojans notre dame wnba nba espn""".split())
def clean(t):
    t = re.sub(r"[^a-z' ]+", " ", t.lower().replace("’", "'"))
    return " ".join(w for w in t.split() if w not in STOP and len(w) > 2)
rows = defaultdict(lambda: {"fox": [], "others": []})
for r in csv.DictReader((HERE / "data" / "player_sentences.csv").open()):
    if r["date"] < FROM: continue
    rows[r["player"]]["fox" if r["outlet"] == "Fox News" else "others"].append(r["sentence"])
out = {}
for player, sides in rows.items():
    fox, oth = sides["fox"], sides["others"]
    if len(fox) < MIN_SENTENCES or len(oth) < MIN_SENTENCES: continue
    fc, oc = [clean(s) for s in fox], [clean(s) for s in oth]
    cv = CV(decode_error="ignore", min_df=4, max_df=.5, ngram_range=(2, 2), max_features=20000, token_pattern=r"(?u)\b\w[\w'-]*\w\b")
    scored = bayes_compare_language(fc, oc, prior=.05, cv=cv)
    cv.fit(fc + oc)
    f_ct, o_ct = cv.transform(fc).sum(axis=0).A1, cv.transform(oc).sum(axis=0).A1
    idx = {t: i for i, t in enumerate(cv.get_feature_names_out())}
    # capitalisation in the raw text, counted once per player: a proper noun
    # is capitalised wherever it occurs
    pair_total, pair_caps = Counter(), Counter()
    for s in fox + oth:
        toks = re.findall(r"[A-Za-z][\w'-]*", s.replace("’", "'"))
        for a, b in zip(toks, toks[1:]):
            key = f"{a.lower()} {b.lower()}"
            pair_total[key] += 1
            if a[0].isupper() and b[0].isupper():
                pair_caps[key] += 1
    def cap_share(phrase):
        return pair_caps[phrase] / pair_total[phrase] if pair_total[phrase] else 0
    def example(phrase, pool):
        pat = re.compile(r"\b" + re.escape(phrase.split()[0]) + r"\s+" + re.escape(phrase.split()[1]) + r"\b", re.I)
        for s in pool:
            m = pat.search(s)
            if m and len(s) <= 320: return s.strip(), m.group(0)
        return "", ""
    sides_out = {"clark": [], "others": []}
    # strongest first on both sides: bayes_compare_language returns the scores
    # in ascending order, so reading it straight gave Fox's side the phrases
    # nearest zero (fixed 2026-09-30)
    for phrase, z in sorted(scored, key=lambda t: -abs(t[1])):
        i = idx.get(phrase)
        if i is None: continue
        nf, no = int(f_ct[i]), int(o_ct[i])
        if nf + no < MIN_PAIR or BAD.search(phrase) or cap_share(phrase) >= 0.7: continue
        if any(re.sub(r"'s?$", "", t) in NAME_PARTS for t in phrase.split()): continue
        side = "clark" if z > 0 else "others"
        if len(sides_out[side]) >= TOP: continue
        eg, egw = example(phrase, fox if side == "clark" else oth)
        sides_out[side].append({"word": phrase, "z": round(abs(float(z)), 2), "clark": nf, "others": no, "top": True, "eg": eg, "egw": egw})
    sides_out["others"].sort(key=lambda w: -w["z"])
    out[player] = {"scored": sides_out, "counts": {"clark": len(fox), "others": len(oth)}}
    print(f"{player:20} Fox {len(fox):5} · others {len(oth):5} · {[w['word'] for w in sides_out['clark'][:5]]}", flush=True)
(HERE / "src" / "data" / "player_phrases.json").write_text(json.dumps(out, ensure_ascii=False))
print(f"{len(out)} players written")
