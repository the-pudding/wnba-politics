"""
Terms are in data/framing_terms.csv 
"""
import csv
import re
from collections import defaultdict
from pathlib import Path

TERMS_CSV = Path(__file__).resolve().parent.parent / "data" / "framing_terms.csv"


def load_terms():
    """Read the CSV fresh every call, so edits show up without restarting the kernel."""
    terms = defaultdict(list)
    for row in csv.DictReader(open(TERMS_CSV)):
        terms[(row["register"], row["kind"])].append(row["term"])
    return terms


def term_set(register, kind):
    return set(load_terms()[(register, kind)])


def rx(register, kind):
    """rows OR-ed inside \\b(...)\\b, case-insensitive"""
    return re.compile(r"\b(" + "|".join(load_terms()[(register, kind)]) + r")\b", re.I)


def scrub_rx(register):
    terms = load_terms().get((register, "scrub"))
    return re.compile(r"\b(" + "|".join(terms) + r")\b", re.I) if terms else None


def by_her_rx(surname_of):
    """{player: regex} — she is the one delivering the contact"""
    verbs = "|".join(load_terms()[("victim", "by_her_verb")])
    # the surname must be capitalized (Brink the player, not "the brink of");
    # the verbs still match in any case
    return {name: re.compile(
        rf"\b{re.escape(last)}\b[^.]{{0,24}}\b(?i:{verbs})\b")
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
    for name in groups:
        # whole words only ("Bout" must not match inside "about") and
        # capitalized only ("Brink" the player, not "the brink of")
        for m in re.finditer(r"\b" + re.escape(name.split()[-1]) + r"\b", headline[:before]):
            if m.start() > where:
                best, where = name, m.start()
    return best


def clean(text):
    # lowercase, drop a possessive 's, trim stray punctuation (never letters)
    return re.sub(r"['’]s$", "", text.lower()).strip(",'’\"")


def leans_on_name(token):
    """ "husband Darren Waller": the noun modifies a proper name, so the
    possessor is implied — the sentence's subject owns it."""
    return token.head.pos_ == "PROPN" or any(
        c.pos_ == "PROPN" and c.dep_ in ("appos", "flat", "compound") for c in token.children)


def words_under(tokens):
    return {clean(sub.text) for t in tokens for sub in t.subtree}


from lookalikes import mask

WATCH_TAG = re.compile(r"^\s*WATCH\s*:\s*|\s*[:|]\s*WATCH\s*$|\s*\(WATCH\)")


def untag(text):
    return WATCH_TAG.sub(" ", text)


def attribute(nlp, headlines, groups, register, name_rx=None):
    """{player: [headline rows]} each qualifying headline is grammatically about.

    Every word row in framing_terms.csv is a trigger, whatever its kind
    (noun, verb, adjective...) — multi-word phrases like "tiktok followers"
    work too, judged by their last word. One row per term is all it takes."""
    # every term is a pattern (framing_terms.csv holds regexes such as
    # "scor(?:es|ed|ing)" and "\\d+ points" beside plain words): a match in the
    # sentence text is pinned to the token holding its last character, and
    # ownership is judged from that token (a literal word test would never
    # fire for the performance register's patterns)
    trigger_terms = set().union(*[terms for (reg, kind), terms in load_terms().items()
                                  if reg == register and kind not in ("prefilter", "scrub")])
    # whole words only: without the boundaries "dress" matched inside "address"
    # and "hair" inside "chair"
    trigger_rx = re.compile(r"\b(?:" + "|".join(rf"(?:{t})" for t in sorted(trigger_terms, key=len, reverse=True)) + r")\b", re.I) if trigger_terms else None
    scrub = scrub_rx(register)
    # look-alikes' surnames blanked ("Ryan Clark" -> "Ryan Cxxxx", same length)
    # so the surname test below cannot hand his words to Caitlin
    # and a video tag ("WATCH:", ": WATCH") dropped: the parser takes it for
    # the headline's main word and loses who the rest is about
    text_for = (lambda r: scrub.sub(" ", untag(mask(r["t"])))) if scrub else (lambda r: untag(mask(r["t"])))
    attributed = defaultdict(list)
    for row, doc in zip(headlines, nlp.pipe([text_for(r) for r in headlines], batch_size=64)):
        # who is in the headline: each person's own pattern from people.json
        # when given (so "West Wilson" is not A'ja), else the surname,
        # capitalized — "Brink" the player, never "the brink of suspension"
        present = [name for name in groups
                   if (name_rx[name].search(row["t"]) if name_rx and name in name_rx
                       else re.search(r"\b" + re.escape(name.split()[-1]) + r"\b", row["t"]))]
        owners_found, pronoun_at = set(), None
        hits = []
        if trigger_rx is not None:
            for m in trigger_rx.finditer(doc.text):
                last = m.end() - 1
                tok = next((t for t in doc if t.idx <= last < t.idx + len(t.text)), None)
                if tok is not None and (not hits or hits[-1].i != tok.i):
                    hits.append(tok)
        for hit in hits:
            owned = words_under(owner_tokens(hit, doc))
            direct = False
            for name in present:
                if name.split()[-1].lower() in owned:
                    owners_found.add(name)
                    direct = True
            if not direct and leans_on_name(hit):
                root = next((t for t in doc if t.dep_ == "ROOT"), None)
                if root is not None:
                    subject_words = words_under([c for c in root.children if c.dep_ in SUBJECT_DEPS])
                    for name in present:
                        if name.split()[-1].lower() in subject_words:
                            owners_found.add(name)
            if owned & PRONOUNS:
                pronoun_at = min(pronoun_at, hit.idx) if pronoun_at is not None else hit.idx
        if not owners_found and pronoun_at is not None:
            who = nearest_named(mask(row["t"]), present, pronoun_at)
            if who:
                owners_found.add(who)
        for name in owners_found:
            attributed[name].append(row)
    return attributed


# Politicization terms match as prefixes ("racis" catches racism and racist),
# so a short term can swallow unrelated words: "trans" matched "transition",
# "transfer", "transaction". Each guarded term gets the endings it must not have.
PREFIX_GUARDS = {
    "trans": r"trans(?!ition|fer|act|cript|lat|port|parent|form|mit|it\b|itio|ist|pire|cend|plant|atlantic|continental|lucent|vers|gress|mission|pos|ferr)",
}
def guard_term(term):
    """The regex for one politicization term, with its false-prefix guard."""
    return PREFIX_GUARDS.get(term.strip().lower(), term)
