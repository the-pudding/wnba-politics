"""Word forms grouped under their base form for the Fightin' Words charts
("posted", "posts" -> "post"; "competing", "competed" -> "compete"), and how
many articles use each word or phrase.

Each form is tagged in context by spaCy across the article text; a form is
grouped only when spaCy gives it the same base form nearly every time. The
map is cached in notebooks/.cache/fw_lemma_map.json; delete it to rebuild
(about 15 minutes):

    python notebooks/fw_groups.py
"""
import csv, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE / ".cache" / "fw_lemma_map.json"

# ---------------------------------------------------------------------------
# Edit these
# ---------------------------------------------------------------------------

# the parts of speech whose forms are grouped: plurals and verb tenses.
# Adjectives keep their degrees apart ("big", "bigger", "biggest")
GROUPED_POS = {"NOUN", "VERB"}
# how often a form must get the same base form to be grouped under it
SAME_LEMMA_SHARE = 0.9
# forms left as written: their base form means something else here
KEEP_AS_IS = {"media", "data", "news", "left", "saw", "felt", "found", "lives", "rights",
              "arms", "glasses", "goods", "means", "odds", "times", "terms", "relations",
              "remains", "spirits"}
# plurals grouped under their singular by hand, where the rule above misses
# them (the singular is mostly used as an adjective: "male", "star"). Only
# true plurals: "seconds", "finals", "wings", "forwards" mean something else
PLURALS = {"stars": "star", "arenas": "arena", "conferences": "conference", "champions": "champion",
           "averages": "average", "hosts": "host", "americans": "american", "sides": "side",
           "rankings": "ranking", "females": "female", "males": "male", "squads": "squad",
           "images": "image", "ladies": "lady", "racists": "racist", "wars": "war"}

# ---------------------------------------------------------------------------


def build_map(texts, n_process=2):
    """{form: base form} from the texts, tagged in context"""
    import spacy
    nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
    seen = defaultdict(Counter)     # form -> (lemma, pos) counts
    for doc in nlp.pipe(texts, n_process=n_process, batch_size=64):
        for tok in doc:
            if tok.is_alpha:
                seen[tok.lower_][(tok.lemma_.lower(), tok.pos_)] += 1
    # each form's usual part of speech, so a base form that is mostly another
    # kind of word ("right" for "rights") is not where the form goes
    usual_pos = {}
    for form, counts in seen.items():
        by_pos = Counter()
        for (_, pos), n in counts.items():
            by_pos[pos] += n
        usual_pos[form] = by_pos.most_common(1)[0][0]
    out = {}
    for form, counts in seen.items():
        if form in KEEP_AS_IS:
            continue
        total = sum(counts.values())
        by_lemma = Counter()
        for (lemma, pos), n in counts.items():
            if pos in GROUPED_POS:
                by_lemma[lemma] += n
        if not by_lemma:
            continue
        lemma, n = by_lemma.most_common(1)[0]
        if (lemma != form and lemma.isalpha() and n >= SAME_LEMMA_SHARE * total
                and lemma in seen and usual_pos.get(lemma) in GROUPED_POS):
            out[form] = lemma
    return out


def dropped_e(groups):
    """The forms whose base form lost a final "e" ("hated" under "hat",
    "riding" under "rid", where "hate" and "ride" are words): left as written"""
    words = Path("/usr/share/dict/words")
    known = {w.strip().lower() for w in words.open()} if words.exists() else set()
    # the short words that end consonant-vowel-consonant, where a silent "e"
    # goes missing ("hop" for "hope"); "pass", "form", "visit" are left alone
    short_cvc = lambda w: len(w) <= 4 and re.search(r"(?:^|[^aeiou])[aeiou][^aeiouwxy]$", w)
    return {form for form, lemma in groups.items()
            if form in (lemma + "ing", lemma + "ed", lemma + "es")
            and short_cvc(lemma) and lemma + "e" in known}


def lemma_map(texts=None):
    if CACHE.exists():
        out = json.loads(CACHE.read_text())
    else:
        out = build_map(texts)
        CACHE.parent.mkdir(exist_ok=True)
        CACHE.write_text(json.dumps(out, ensure_ascii=False, sort_keys=True))
    wrong = dropped_e(out)
    return {**{form: lemma for form, lemma in out.items() if form not in wrong}, **PLURALS}


def presence(keys, docs_by_outlet, n):
    """For each key (an n-word phrase, as the docs write it): per outlet, how
    many articles use it"""
    want = set(keys)
    articles = defaultdict(Counter)
    for outlet, docs in docs_by_outlet.items():
        for doc in docs:
            toks = doc.split()
            for g in {" ".join(toks[j:j + n]) for j in range(len(toks) - n + 1)} & want:
                articles[g][outlet] += 1
    return articles


if __name__ == "__main__":
    # the matched window's article text, every outlet notebook 06 reads
    sys.path.insert(0, str(HERE))
    from outlets import OUTLETS
    csv.field_size_limit(10 ** 9)
    texts = []
    for key, *_ in OUTLETS:
        for row in csv.DictReader((HERE.parent / "data" / f"{key}.csv").open()):
            if (row.get("date") or "")[:10] >= "2023-04-01":
                texts.append(((row.get("headline") or "") + "\n" + (row.get("body") or "")).strip())
    if CACHE.exists():
        CACHE.unlink()
    m = lemma_map(texts)
    print(f"{len(m):,} forms grouped, e.g.", sorted(m.items())[:12])
