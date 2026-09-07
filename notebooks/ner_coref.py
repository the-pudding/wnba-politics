"""
Who does Fox News talk about? People mentions across the Fox WNBA corpus,
headline and full text, with coreference.

For every article, spaCy's transformer NER finds PERSON spans and fastcoref
(F-Coref) groups the mentions that refer to the same person: the full name,
the surname on later reference, "she", "her", "the rookie". A coreference
cluster counts as a person when any of its mentions is a PERSON span; every
mention in it then counts for that person. PERSON spans outside any cluster
count once each.

Names are unified within a document first (a bare "Clark" attaches to the
full name that ends in Clark in the same article) and then across the
corpus (a bare surname on its own maps to the corpus's most frequent full
name ending in it).

Output: data/fox_people_mentions.csv, one row per person, ranked by mentions
(with coreference), plus named-only mentions, headline mentions, and the
number of articles naming them.

Requirements: spacy (en_core_web_trf), fastcoref, pandas

    python notebooks/ner_coref.py            # full corpus (cached per article)
    python notebooks/ner_coref.py --limit 30 # a pilot

Per-article results are cached in notebooks/.cache/ner_coref.jsonl, so a
re-run only processes new articles.
"""

import argparse
import html
import json
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ROSTER = ROOT / "src" / "data" / "people.json"
CORPUS = ROOT / "data" / "fox_wnba.csv"
CACHE = ROOT / "notebooks" / ".cache" / "ner_coref.jsonl"
OUT = ROOT / "data" / "fox_people_mentions.csv"

NER_MODEL = "en_core_web_trf"
BATCH = 16

# --- name normalisation ------------------------------------------------------
TITLES = re.compile(
    r"^(?:mr|mrs|ms|dr|sen|rep|gov|coach|president|vice president|vp|"
    r"sens|reps|senator|congresswoman|congressman|commissioner|judge|"
    r"attorney general)\.?\s+",
    re.I,
)
POSSESSIVE = re.compile(r"(?:'s|’s|'|’)$")
EDGE_NOISE = "\"“”‘’'()[] ,.:;-—"
# the same person under a nickname (Bill Laimbeer / William Laimbeer)
NICKNAMES = {
    "bill": "william", "billy": "william", "will": "william",
    "mike": "michael", "jim": "james", "jimmy": "james", "bob": "robert",
    "rob": "robert", "tom": "thomas", "dave": "david", "steve": "stephen",
    "chris": "christopher", "joe": "joseph", "tony": "anthony", "dick": "richard",
    "rick": "richard", "ben": "benjamin", "sam": "samuel", "alex": "alexander",
    "matt": "matthew", "dan": "daniel", "danny": "daniel", "andy": "andrew",
    "ed": "edward", "ted": "edward", "kate": "katherine", "katie": "katherine",
    "liz": "elizabeth", "beth": "elizabeth", "jen": "jennifer", "jenny": "jennifer",
    "becky": "rebecca", "sue": "susan", "steph": "stephanie",
}


def clean_text(text):
    """Article text as NER should see it: entities decoded, odd spaces plain."""
    t = html.unescape(str(text)).replace("\xa0", " ")
    return re.sub(r"[ \t]+", " ", t)


# words NER sometimes sweeps into a name from the text around it
LEAD_NOISE = {
    "this", "that", "more", "center", "guard", "forward", "star", "rookie",
    "coach", "the", "a", "an", "and", "but", "with", "for", "by", "to", "of",
    "veteran", "former", "then", "now", "sophomore", "freshman", "junior",
    "senior", "teammate", "teammates", "fever", "sky", "liberty", "aces",
}


def clean_name(text):
    """A PERSON span as a name: no possessive, title, quotes, stray punctuation,
    or the words NER swept up from around it."""
    t = text.replace("’", "'").strip(EDGE_NOISE)
    t = TITLES.sub("", t)
    t = POSSESSIVE.sub("", t).strip(EDGE_NOISE)
    toks = t.split()
    # "This Paige Bueckers", "anti-President Trump", "PAUL WHELAN Griner"
    while toks and (
        toks[0].lower() in LEAD_NOISE
        or not toks[0][0].isupper()
        or (toks[0].isupper() and len(toks[0]) > 1)
    ):
        toks = toks[1:]
    while toks and toks[-1].isupper() and len(toks[-1]) > 1:
        toks = toks[:-1]
    # "Moore Maya Moore"
    if len(toks) > 2 and toks[0].lower() == toks[-1].lower():
        toks = toks[1:]
    return " ".join(toks)


def name_key(name):
    """Tokens for matching: lower-case, nicknames unfolded, no punctuation."""
    toks = [re.sub(r"[^a-z']", "", t.lower()) for t in name.replace("’", "'").split()]
    toks = [t for t in toks if t]
    if toks:
        toks[0] = NICKNAMES.get(toks[0], toks[0])
    return tuple(toks)


def is_short_form(short, full):
    """How `short` refers to `full`: "suffix" (a surname, "Delle Donne"),
    "prefix" (a first name), or False."""
    a, b = name_key(short), name_key(full)
    if not a or not b or len(a) >= len(b):
        return False
    if b[-len(a):] == a:
        return "suffix"
    if b[: len(a)] == a:
        return "prefix"
    return False


def may_merge(kind, short_named, full_named):
    """A surname or a bare first name always joins the fuller name; a full name
    only extends forward ("Caitlin Clark" -> "Caitlin Clark Silver") when the
    longer form is at least as common, which the junk never is."""
    return kind == "suffix" or (kind == "prefix" and full_named >= short_named)


# who a bare surname means when no article says: the site's roster first
# (Clark is Caitlin, Biden is Joe), then a few the roster lacks
def roster_aliases():
    aliases = {}
    try:
        roster = json.loads(ROSTER.read_text())
    except FileNotFoundError:
        return aliases
    for person, info in roster.items():
        for alt in info.get("rx", "").split("|"):
            word = re.sub(r"\\b|\(\?<!.*?\)|\(\?!.*?\)|\\|\?", "", alt).strip()
            if word and " " not in word and "." not in word:
                aliases[word.lower()] = person
    return aliases


ALIASES = {
    "watkins": "JuJu Watkins",
    "harris": "Kamala Harris",
    "vance": "J.D. Vance",
    "staley": "Dawn Staley",
    "swift": "Taylor Swift",
    "kelce": "Travis Kelce",
    **roster_aliases(),
}


def is_namelike(name):
    """Drop spans NER calls PERSON that are not a person's name."""
    if len(name) < 2 or len(name) > 40:
        return False
    if not re.search(r"[A-Za-z]", name):
        return False
    if name.lower() in {"fox news", "outkick", "wnba", "nba", "espn"}:
        return False
    # all-caps site furniture ("CLICK HERE", "FOX NEWS APP")
    if name.isupper() and len(name) > 3:
        return False
    return True


# --- the models --------------------------------------------------------------
def load_models():
    import spacy
    import torch
    from fastcoref import FCoref

    spacy.prefer_gpu()
    nlp = spacy.load(NER_MODEL, disable=["parser", "lemmatizer", "attribute_ruler"])
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    coref = FCoref(device=device, enable_progress_bar=False)
    return nlp, coref


def analyse(texts, nlp, coref):
    """PERSON spans and coreference clusters, as character offsets, per text."""
    docs = list(nlp.pipe(texts, batch_size=BATCH))
    persons = [
        [(e.start_char, e.end_char, e.text) for e in d.ents if e.label_ == "PERSON"]
        for d in docs
    ]
    preds = coref.predict(texts=texts)
    clusters = [p.get_clusters(as_strings=False) for p in preds]
    return persons, clusters


# --- turning spans and clusters into people ----------------------------------
def overlaps(a, b):
    return a[0] < b[1] and b[0] < a[1]


def resolve_document(text, head_len, persons, clusters):
    """
    Mentions per person in one article.

    Returns {name: {"mentions": n, "named": n, "headline": n}} where `name`
    is the document's best name for the person (the longest PERSON string in
    the cluster), before corpus-level unification.
    """
    persons = [(s, e, clean_name(t)) for s, e, t in persons]
    persons = [(s, e, n) for s, e, n in persons if is_namelike(n)]

    counts = {}
    used = [False] * len(persons)

    def add(name, span, named):
        row = counts.setdefault(name, {"mentions": 0, "named": 0, "headline": 0})
        row["mentions"] += 1
        row["named"] += named
        row["headline"] += span[0] < head_len

    for cluster in clusters:
        # the PERSON spans this cluster's mentions cover
        hits = []
        for m in cluster:
            for i, (s, e, n) in enumerate(persons):
                if overlaps(m, (s, e)):
                    hits.append((i, n))
        if not hits:
            continue
        # the person's name: the form used most in the article, then the fuller
        freq = Counter(n for _, n in hits)
        name = max(freq, key=lambda n: (freq[n], len(n.split()), len(n)))
        for i, _ in hits:
            used[i] = True
        hit_spans = {i for i, _ in hits}
        for m in cluster:
            named = any(overlaps(m, (persons[i][0], persons[i][1])) for i in hit_spans)
            add(name, m, named)

    # PERSON spans no cluster touched
    for i, (s, e, n) in enumerate(persons):
        if not used[i]:
            add(n, (s, e), True)

    # spellings with the same key (Bill / William Laimbeer, A'ja / A’ja) are
    # one name: the spelling with more named mentions
    by_key = defaultdict(list)
    for name in counts:
        by_key[name_key(name)].append(name)
    if any(len(v) > 1 for v in by_key.values()):
        collapsed = {}
        for variants in by_key.values():
            keep = max(variants, key=lambda n: (counts[n]["named"], len(n)))
            dst = collapsed.setdefault(keep, {"mentions": 0, "named": 0, "headline": 0})
            for v in variants:
                for k in dst:
                    dst[k] += counts[v][k]
        counts = collapsed

    # a shorter form ("Clark", "Delle Donne") joins the fuller name in the
    # same article; with several, the one named most often
    merged = {}
    for name, row in counts.items():
        target = name
        fuller = [
            f
            for f in counts
            if f != name
            and may_merge(is_short_form(name, f), row["named"], counts[f]["named"])
        ]
        if fuller:
            target = max(fuller, key=lambda f: counts[f]["named"])
        dst = merged.setdefault(target, {"mentions": 0, "named": 0, "headline": 0})
        for k in dst:
            dst[k] += row[k]
    return merged


def unify_corpus(per_doc):
    """
    Corpus-level names: a short form (a bare surname or first name, a name
    missing a middle part, a nickname) maps to the most frequent fuller name
    it fits; names with the same key (A'ja / A’ja) collapse together.
    Returns {doc_name: canonical}.
    """
    named_total = Counter()
    for doc in per_doc:
        for name, row in doc.items():
            named_total[name] += row["named"]
    # spelling variants with the same key: the most frequent spelling wins
    by_key = defaultdict(list)
    for name in named_total:
        by_key[name_key(name)].append(name)
    spelling = {k: max(v, key=lambda n: named_total[n]) for k, v in by_key.items()}
    # fuller names indexed by every suffix and prefix of their tokens
    fuller_by_part = defaultdict(list)
    for key, name in spelling.items():
        for i in range(1, len(key)):
            fuller_by_part[key[i:]].append(name)
            fuller_by_part[key[:i]].append(name)

    canon = {}
    for name in named_total:
        key = name_key(name)
        base = spelling[key]
        if len(key) == 1 and key[0] in ALIASES:
            canon[name] = ALIASES[key[0]]
            continue
        cands = [
            f
            for f in fuller_by_part.get(key, [])
            if name_key(f) != key
            and may_merge(is_short_form(base, f), named_total[base], named_total[f])
        ]
        canon[name] = max(cands, key=lambda f: named_total[f]) if cands else base
    # an alias target spelled differently in the corpus (A'ja / A’ja) still lands on it
    for name, target in list(canon.items()):
        k = name_key(target)
        if k in spelling and spelling[k] != target and target not in named_total:
            canon[name] = spelling[k]
    return canon
    return canon


# --- the run -----------------------------------------------------------------
def article_text(r):
    """Headline and body as one text, and where the headline ends."""
    head = clean_text(r.headline).strip()
    body = clean_text(r.body).strip()
    return f"{head}\n\n{body}".strip(), len(head)


def load_cache():
    rows = {}
    if CACHE.exists():
        for line in CACHE.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                rows[r["url"]] = r
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="pilot on N articles")
    ap.add_argument("--top", type=int, default=40)
    args = ap.parse_args()

    df = pd.read_csv(CORPUS).fillna("")
    df = df.drop_duplicates("url")
    if args.limit:
        df = df.head(args.limit)
    print(f"{len(df):,} articles", file=sys.stderr)

    cache = load_cache()
    todo = df[~df.url.isin(cache)]
    if len(todo):
        print(f"analysing {len(todo):,} new articles…", file=sys.stderr)
        nlp, coref = load_models()
        CACHE.parent.mkdir(exist_ok=True)
        t0 = time.time()
        done = 0
        with CACHE.open("a") as fh:
            for start in range(0, len(todo), BATCH):
                chunk = todo.iloc[start : start + BATCH]
                texts = [article_text(r)[0] for r in chunk.itertuples()]
                persons, clusters = analyse(texts, nlp, coref)
                for r, text, p, c in zip(chunk.itertuples(), texts, persons, clusters):
                    row = {
                        "url": r.url,
                        "date": r.date,
                        "head_len": article_text(r)[1],
                        "persons": p,
                        "clusters": c,
                    }
                    cache[r.url] = row
                    fh.write(json.dumps(row) + "\n")
                done += len(chunk)
                rate = done / (time.time() - t0)
                left = (len(todo) - done) / rate if rate else 0
                print(
                    f"  {done:,}/{len(todo):,}  {rate:.1f} articles/s  ~{left/60:.0f} min left",
                    file=sys.stderr,
                )

    # resolve each article, then unify names across the corpus
    per_doc = []
    dates = []
    for r in df.itertuples():
        c = cache[r.url]
        text, _ = article_text(r)
        per_doc.append(resolve_document(text, c["head_len"], c["persons"], c["clusters"]))
        dates.append(r.date)
    canon = unify_corpus(per_doc)

    people = {}
    for doc, date in zip(per_doc, dates):
        seen = set()
        for name, row in doc.items():
            person = canon.get(name, name)
            p = people.setdefault(
                person,
                {
                    "mentions": 0,
                    "named": 0,
                    "headline": 0,
                    "articles": 0,
                    "first": date,
                    "last": date,
                },
            )
            for k in ("mentions", "named", "headline"):
                p[k] += row[k]
            if person not in seen:
                p["articles"] += 1
                seen.add(person)
            p["first"] = min(p["first"], date)
            p["last"] = max(p["last"], date)

    out = (
        pd.DataFrame(
            [
                {
                    "person": name,
                    "mentions": p["mentions"],
                    "named_mentions": p["named"],
                    "headline_mentions": p["headline"],
                    "articles": p["articles"],
                    "first_date": p["first"],
                    "last_date": p["last"],
                }
                for name, p in people.items()
            ]
        )
        .sort_values(["mentions", "articles"], ascending=False)
        .reset_index(drop=True)
    )
    out.index += 1
    out.to_csv(OUT, index_label="rank")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(out):,} people)", file=sys.stderr)
    with pd.option_context("display.width", 140, "display.max_rows", 200):
        print(out.head(args.top).to_string())


if __name__ == "__main__":
    main()
