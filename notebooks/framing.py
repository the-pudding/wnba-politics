"""The grammar behind the appearance/celebrity/agency measures.

Vocabularies live in data/framing_terms.csv — one term per row, grouped by
register (appearance, celebrity, agency, victim) and kind. Naming a player in
a headline that also says "outfit" is not enough (the outfit is often somebody
else's), so a term counts for a player only when it is grammatically HERS:
she is its possessor, or the subject of its verb. When the owner is a pronoun,
it resolves to the nearest name in front of it.
"""
import csv
import re
from collections import defaultdict
from pathlib import Path

TERMS_CSV = Path(__file__).resolve().parent.parent / "data" / "framing_terms.csv"

TERMS = defaultdict(list)
for _row in csv.DictReader(open(TERMS_CSV)):
    TERMS[(_row["register"], _row["kind"])].append(_row["term"])


def term_set(register, kind):
    return set(TERMS[(register, kind)])


def rx(register, kind):
    """rows OR-ed inside \\b(...)\\b, case-insensitive"""
    return re.compile(r"\b(" + "|".join(TERMS[(register, kind)]) + r")\b", re.I)


def scrub_rx(register):
    terms = TERMS.get((register, "scrub"))
    return re.compile(r"\b(" + "|".join(terms) + r")\b", re.I) if terms else None


def by_her_rx(surname_of):
    """{player: regex} — she is the one delivering the contact"""
    verbs = "|".join(TERMS[("victim", "by_her_verb")])
    return {name: re.compile(
        rf"\b{re.escape(last)}\b[^.]{{0,24}}\b({verbs})\b", re.I)
        for name, last in surname_of.items()}


SUBJECT_DEPS = {"nsubj", "nsubjpass", "csubj", "agent"}
POSSESSIVE_DEPS = {"poss", "compound", "nmod", "amod"}
PRONOUNS = {"she", "her", "hers", "herself", "they", "them", "their", "theirs", "he", "his", "him"}


def owner_tokens(token, doc):
    """Which tokens own this word — whose outfit is it?"""
    owners = [c for c in token.children if c.dep_ in POSSESSIVE_DEPS]
    node = token
    for _ in range(5):
        head = node.head
        if head is node:
            break
        if head.pos_ in {"VERB", "AUX"}:
            subjects = [c for c in head.children if c.dep_ in SUBJECT_DEPS]
            if subjects:
                owners += subjects
                break
        node = head
    if token.pos_ in {"VERB", "AUX"}:
        owners += [c for c in token.children if c.dep_ in SUBJECT_DEPS]
    if not owners:
        root = next((t for t in doc if t.dep_ == "ROOT"), None)
        if root is not None:
            owners += [c for c in root.children if c.dep_ in SUBJECT_DEPS]
    if not owners:
        owners += list(doc.noun_chunks)[:1]
    return owners


def nearest_named(headline, groups, before):
    """The roster name closest in front of `before` — who a pronoun refers to."""
    best, where = None, -1
    lower = headline.lower()
    for name in groups:
        at = lower.rfind(name.split()[-1].lower(), 0, before)
        if at != -1 and at > where:
            best, where = name, at
    return best


def clean(text):
    # lowercase, drop a possessive 's, trim stray punctuation (never letters)
    return re.sub(r"['’]s$", "", text.lower()).strip(",'’\"")


def words_under(tokens):
    return {clean(sub.text) for t in tokens for sub in t.subtree}


def attribute(nlp, headlines, groups, register):
    """{player: [headline rows]} each qualifying headline is grammatically about.

    Every word row in framing_terms.csv is a trigger, whatever its kind
    (noun, verb, adjective...) — multi-word phrases like "tiktok followers"
    work too, judged by their last word. One row per term is all it takes."""
    trigger_terms = set().union(*[terms for (reg, kind), terms in TERMS.items()
                                  if reg == register and kind not in ("prefilter", "scrub")])
    single = {t for t in trigger_terms if " " not in t}
    phrases = {}
    for t in trigger_terms:
        parts = t.lower().split()
        if len(parts) > 1:
            phrases.setdefault(parts[0], []).append(parts)
    scrub = scrub_rx(register)
    text_for = (lambda r: scrub.sub(" ", r["t"])) if scrub else (lambda r: r["t"])
    attributed = defaultdict(list)
    for row, doc in zip(headlines, nlp.pipe([text_for(r) for r in headlines], batch_size=64)):
        owners_found, pronoun_at = set(), None
        for i, token in enumerate(doc):
            word = clean(token.text)
            hit = token if word in single else None
            if hit is None:
                # a phrase matches when the following tokens spell out the rest;
                # ownership is judged from its last word ("followers", not "tiktok")
                for parts in phrases.get(word, []):
                    rest = [clean(doc[i + j].text) for j in range(1, len(parts)) if i + j < len(doc)]
                    if rest == parts[1:]:
                        hit = doc[i + len(parts) - 1]
                        break
            if hit is None:
                continue
            owned = words_under(owner_tokens(hit, doc))
            for name in groups:
                if name.split()[-1].lower() in owned:
                    owners_found.add(name)
            if owned & PRONOUNS:
                pronoun_at = min(pronoun_at, hit.idx) if pronoun_at is not None else hit.idx
        if not owners_found and pronoun_at is not None:
            who = nearest_named(row["t"], groups, pronoun_at)
            if who:
                owners_found.add(who)
        for name in owners_found:
            attributed[name].append(row)
    return attributed
