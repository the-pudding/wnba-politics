"""The framing measures by sentence rather than by headline.

Every Fox sentence (headline or body) naming someone in the roster's players
and coaches, scored the way 01-player-framing scores headlines: political
(politicization_terms.csv, any group but partisan, a person's own culture-war
words not counting against her), appearance, celebrity (which includes
appearance) and performance (framing_terms.csv), and tone from the same
RoBERTa model as 02-headline-sentiment, cached in data/sentence_sentiment.csv.

Writes src/data/sentence_framing.json: per person, the sentence count, the
mean tone, each measure's share and count, and a few example sentences.

    python3 notebooks/sentence_framing.py            # extract, score, write
"""
import csv, html, json, re, sys, time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import framing

ROOT = Path(__file__).resolve().parents[1]
DATA, OUT = ROOT / "data", ROOT / "src" / "data"
CACHE = DATA / "sentence_sentiment.csv"
MIN_SENTENCES = 30
csv.field_size_limit(10 ** 9)

roster = json.loads((OUT / "people.json").read_text())
people = {n: p for n, p in roster.items() if p.get("group") in ("players", "league")}
name_rx = {n: re.compile(p["rx"], re.I) for n, p in people.items()}

# --- the sentences ------------------------------------------------------------
import spacy
nlp = spacy.blank("en"); nlp.add_pipe("sentencizer"); nlp.max_length = 3_000_000
BOILERPLATE = re.compile(r"CLICK HERE[^a-z]*(?=[A-Z][a-z]|$)")
def clean(t):
    t = html.unescape(str(t or "")).replace("\xa0", " ")
    return re.sub(r"\s+", " ", BOILERPLATE.sub(" ", t)).strip()

rows = list(csv.DictReader((DATA / "fox_wnba.csv").open()))
seen, heads, bodies, meta = set(), [], [], []
for r in rows:
    if r.get("url") in seen: continue
    seen.add(r.get("url")); heads.append(clean(r.get("headline"))); bodies.append(clean(r.get("body")))
    meta.append((r.get("date", "")[:10], r.get("url", "")))
sentences = []   # (date, url, text, [names], is_headline)
def note(date, url, text, is_head):
    who = [n for n, rx in name_rx.items() if rx.search(text)]
    if who: sentences.append((date, url, text, who, is_head))
for (d, u), h in zip(meta, heads):
    if h: note(d, u, h, True)
for (d, u), doc in zip(meta, nlp.pipe(bodies, batch_size=64)):
    for s in doc.sents:
        t = s.text.strip()
        if len(t) >= 15: note(d, u, t, False)
print(f"{len(sentences):,} Fox sentences name someone", file=sys.stderr, flush=True)

# --- the measures, as in 01 ---------------------------------------------------------
groups = defaultdict(list)
for r in csv.DictReader((DATA / "politicization_terms.csv").open()):
    groups[r["group"]].append(r["term"])
group_rx = {g: re.compile("|".join(rf"\b(?:{t})" for t in ts), re.I) for g, ts in groups.items()}
culture_rx = [re.compile(t, re.I) for t in groups.get("culture_war", [])]
# each register's words pooled across its kinds (nouns, verbs, adjectives)
def register_rx(register):
    terms = [t for (reg, kind), ts in framing.load_terms().items() if reg == register and kind != "scrub" for t in ts]
    return re.compile(r"\b(" + "|".join(terms) + r")\b", re.I) if terms else re.compile(r"(?!x)x")
appearance_rx, celebrity_rx, performance_rx = register_rx("appearance"), register_rx("celebrity"), register_rx("performance")
scrub = {k: framing.scrub_rx(k) for k in ("appearance", "celebrity", "performance")}
def political_for(text, person):
    matched = [g for g, rx in group_rx.items() if rx.search(text)]
    if not any(g != "partisan" for g in matched): return False
    if matched == ["culture_war"]:
        own = [rx for rx in culture_rx if rx.search(person)]
        others = [rx for rx in culture_rx if rx not in own]
        return any(rx.search(text) for rx in others)
    return True
def hit(rx, key, text):
    return bool(rx.search(text)) and not (scrub[key] and scrub[key].search(text))

# --- tone, from the cache or the model ------------------------------------------------
scores = {}
if CACHE.exists():
    scores = {r["text"]: float(r["score"]) for r in csv.DictReader(CACHE.open())}
todo = sorted({t for _, _, t, _, _ in sentences} - set(scores))
print(f"{len(scores):,} sentences already scored, {len(todo):,} to score", file=sys.stderr, flush=True)
if todo:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    MODEL = "cardiffnlp/twitter-roberta-large-topic-sentiment-latest"
    LABEL_WEIGHTS = [("strongly negative", -1.0), ("strongly positive", 1.0), ("negative or neutral", 0.0),
                     ("positive or neutral", 0.0), ("negative", -0.6), ("positive", 0.6), ("neutral", 0.0)]
    tok = AutoTokenizer.from_pretrained(MODEL); model = AutoModelForSequenceClassification.from_pretrained(MODEL)
    device = "mps" if torch.backends.mps.is_available() else "cpu"; model.to(device).eval()
    weights = [next((w for ph, w in LABEL_WEIGHTS if ph in model.config.id2label[i].lower()), 0.0) for i in range(model.config.num_labels)]
    with CACHE.open("a", newline="") as fh:
        w = csv.writer(fh)
        if not scores: w.writerow(["text", "score"])
        B, t0 = 32, time.time()
        for i in range(0, len(todo), B):
            chunk = todo[i:i + B]
            enc = tok(chunk, padding=True, truncation=True, max_length=96, return_tensors="pt").to(device)
            with torch.no_grad():
                probs = torch.softmax(model(**enc).logits, dim=-1).cpu().tolist()
            for text, prob in zip(chunk, probs):
                s = round(sum(p * wt for p, wt in zip(prob, weights)), 4); scores[text] = s; w.writerow([text, s])
            if (i // B) % 50 == 0:
                fh.flush(); print(f"  scored {i + len(chunk):,}/{len(todo):,}  ({time.time() - t0:.0f}s)", file=sys.stderr, flush=True)

# --- per person -------------------------------------------------------------------------
per = {}
for name in people:
    mine = [(d, u, t, h) for d, u, t, who, h in sentences if name in who]
    if len(mine) < MIN_SENTENCES: continue
    n = len(mine)
    pol = [t for _, _, t, _ in mine if political_for(t, name)]
    looks = [t for _, _, t, _ in mine if hit(appearance_rx, "appearance", t)]
    celeb = [t for _, _, t, _ in mine if hit(celebrity_rx, "celebrity", t) or hit(appearance_rx, "appearance", t)]
    play = [t for _, _, t, _ in mine if hit(performance_rx, "performance", t)]
    tones = [scores[t] for _, _, t, _ in mine if t in scores]
    ranked = sorted(((scores[t], t) for _, _, t, _ in mine if t in scores))
    per[name] = {
        "group": people[name]["group"], "count": n,
        "tone": round(sum(tones) / max(1, len(tones)), 4),
        "political": round(len(pol) / n, 4), "politicalN": len(pol),
        "appearance": round(len(looks) / n, 4), "appearanceN": len(looks),
        "celebrity": round(len(celeb) / n, 4), "celebrityN": len(celeb),
        "performance": round(len(play) / n, 4), "performanceN": len(play),
        "worst": ranked[0][1] if ranked else "", "best": ranked[-1][1] if ranked else "",
        "politicalExample": pol[0] if pol else "", "appearanceExample": looks[0] if looks else "",
        "celebrityExample": celeb[0] if celeb else "", "performanceExample": play[0] if play else "",
    }
(OUT / "sentence_framing.json").write_text(json.dumps({"minSentences": MIN_SENTENCES, "people": per}))
print(f"wrote sentence_framing.json: {len(per)} people", file=sys.stderr)
for name, p in sorted(per.items(), key=lambda kv: -kv[1]["count"])[:12]:
    print(f"  {name:20} {p['count']:6} sentences  tone {p['tone']:+.3f}  political {p['political']:.0%}  looks {p['appearance']:.1%}  celebrity {p['celebrity']:.1%}  play {p['performance']:.0%}", file=sys.stderr)
