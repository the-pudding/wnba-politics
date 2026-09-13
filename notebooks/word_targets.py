"""Who is a word *about*? Coreference plus a dependency parse.

The per-player charts count sentences that mention a player and contain a
word. That can't tell "Carrington's dirty foul on Cunningham" apart from
"Cunningham's dirty foul on Carrington": both players are in the sentence.
This script reads every article that uses the word, resolves pronouns and
surnames back to people with fastcoref, and walks the dependency tree around
each use to decide who the word is attached to:

    accused   the person the word describes, or whose act it describes
              ("Carrington's dirty foul", "Carrington committed a dirty play",
              "she is a dirty player", "called Carrington dirty")
    victim    the person on the receiving end
              ("dirty foul on Cunningham", "dirty play that injured Cunningham")

Usage:
    python notebooks/word_targets.py dirty
    python notebooks/word_targets.py dirty --show      # print every use with its reading

Writes static/data/word_targets/<word>.json with per-player counts by side.
"""
import json, re, sys, warnings
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent.parent
OUTLETS = {
    "Fox News": HERE / "data" / "fox_wnba.csv",
    "ESPN": HERE / "data" / "espn.csv",
    "CBS Sports": HERE / "data" / "cbs_sports.csv",
    "USA Today": HERE / "data" / "usa_today.csv",
    "The Athletic": HERE / "data" / "the_athletic.csv",
    "Just Women's Sports": HERE / "data" / "just_womens_sports.csv",
}
PEOPLE = json.loads((HERE / "src" / "data" / "people.json").read_text())
NAME_RX = {name: re.compile(info["rx"], re.I) for name, info in PEOPLE.items()}
MAX_CHARS = 12000     # fastcoref is quadratic-ish; the bodies are capped anyway

# what a "dirty X" can be: an act (play, foul) or a person (player)
ACT_NOUNS = {"play", "foul", "hit", "tactic", "elbow", "shot", "move", "stuff", "basketball",
             "contact", "thing", "game", "shove", "push", "screen", "trip", "act", "action",
             "behavior", "behaviour", "style", "reputation", "history",
             # traits, for words that are nouns themselves: "Clark's basketball IQ"
             "iq", "intelligence", "grit", "toughness", "hustle", "mentality", "effort",
             "attitude", "defense", "energy", "intensity", "edge", "presence", "role"}
PERSON_NOUNS = {"player", "one", "athlete", "team", "girl", "guard", "forward", "center", "star",
                "enforcer", "villain", "bully", "hero", "leader", "competitor", "rookie", "veteran",
                "teammate", "defender", "scorer", "shooter", "rebounder", "playmaker"}
# nouns whose "dirty" has nothing to do with a person: dirty work, dirty money
IGNORE_NOUNS = {"work", "money", "trick", "blanket", "laundry", "cheater", "word", "look",
                "secret", "joke", "bomb", "water", "air", "hand", "dozen"}
# verbs whose subject is the doer of a "dirty X"
DOER_VERBS = {"commit", "deliver", "make", "have", "throw", "do", "pull", "get", "give", "play", "be"}
# verbs whose object the word is being applied to: "called Carrington dirty"
LABEL_VERBS = {"call", "label", "consider", "deem", "describe", "brand", "see", "view"}
# prepositions pointing at the person on the receiving end
VICTIM_PREPS = {"on", "against", "to", "toward", "towards", "at"}
DOER_PREPS = {"by", "from"}
# "Clark has been the target of ... dirty plays"
RECEIVER_NOUNS = {"target", "victim", "recipient", "end", "subject"}
# "defended Thomas against accusations of dirty play"
ACCUSATION_NOUNS = {"accusation", "criticism", "reputation", "description", "label", "claim", "charge", "narrative"}
# "earned Cunningham the nickname 'the enforcer'", "Cunningham's enforcer role"
NICK_NOUNS = {"nickname", "title", "label", "role", "moniker", "tag", "reputation", "name", "identity"}
REL_PRONOUNS = {"who", "that", "which", "whom"}
SURNAME = {}
for _name in PEOPLE:
    SURNAME.setdefault(_name.split()[-1].lower(), []).append(_name)
SURNAME = {k: v[0] for k, v in SURNAME.items() if len(v) == 1 and len(k) > 3}


def who(span_text):
    """Roster name for a mention, or None."""
    for name, rx in NAME_RX.items():
        if rx.search(span_text):
            return name
    # a bare surname the roster regex is too strict for ("Carter's dirty play")
    for tok in re.findall(r"[A-Za-z]+", span_text):
        if tok.lower() in SURNAME and tok[:1].isupper():
            return SURNAME[tok.lower()]
    return None


def resolve(doc, clusters, tok):
    """The person a token refers to: a name in its coreference cluster, or a
    name in the token's own subtree ('Carrington's' → Carrington)."""
    start = tok.idx
    for cluster in clusters:
        hit = any(a <= start < b for a, b in cluster)
        if not hit:
            continue
        for a, b in cluster:
            name = who(doc.text[a:b])
            if name:
                return name
    return who("".join(t.text_with_ws for t in tok.subtree))


def lem(t):
    return t.lemma_.lower()


def subject_of(verb):
    """The clause's subject; a relative pronoun hands back the noun it stands for."""
    for child in verb.children:
        if child.dep_ in {"nsubj", "nsubjpass"}:
            if lem(child) in REL_PRONOUNS and verb.dep_ == "relcl":
                return verb.head
            return child
    # "Clark is so driven and has such a high IQ": the second verb shares the subject
    if verb.dep_ == "conj" and verb.head is not verb:
        return subject_of(verb.head)
    return None


def readings(doc, clusters, tok):
    """(role, token) pairs for one use of the word."""
    out = []
    # "relentless or dirty", "an enforcer or a dirty player": read the word (and
    # its noun) through the coordination it sits in
    anchor = tok
    while anchor.dep_ == "conj":
        anchor = anchor.head
    head = anchor.head
    is_noun = tok.pos_ in {"NOUN", "PROPN"} and tok.dep_ not in {"amod", "compound"}
    if is_noun or tok.dep_ == "amod" or (tok.dep_ == "compound" and tok.head.pos_ == "NOUN"):
        # the word is a noun itself ("enforcer", "IQ") or modifies one ("dirty play")
        noun = tok if is_noun else tok.head
        if lem(noun) in IGNORE_NOUNS:
            return []
        person_noun = lem(noun) in PERSON_NOUNS or (is_noun and lem(tok) in PERSON_NOUNS)
        # "Cunningham, the Fever's enforcer" / "an enforcer like Cunningham"
        if is_noun and noun.dep_ == "appos":
            out.append(("accused", noun.head))
        # "the gritty point guard retired", "picked up the gritty guard": the
        # noun phrase itself names the person, and coreference says who
        if person_noun and not is_noun and noun.dep_ in {"nsubj", "nsubjpass", "dobj", "pobj", "appos", "conj"}:
            out.append(("accused", noun))
        # "earned Cunningham the nickname 'the enforcer'", "Cunningham's enforcer role",
        # "Cunningham, who has taken on the role of enforcer"
        for anc in [noun] + list(noun.ancestors)[:3]:
            if lem(anc) in NICK_NOUNS and anc is not noun or (anc is noun and tok.dep_ == "compound" and lem(anc) in NICK_NOUNS):
                out += [("accused", c) for c in anc.children if c.dep_ == "poss"]
                verb = anc.head
                while verb.dep_ in {"prep", "pobj"} and verb.head is not verb:
                    verb = verb.head
                if verb.pos_ in {"VERB", "AUX"}:
                    dative = [c for c in verb.children if c.dep_ == "dative"]
                    if dative:
                        out += [("accused", d) for d in dative]
                    else:
                        subj = subject_of(verb)
                        if subj:
                            out.append(("accused", subj))
                break
        for child in noun.children:
            if child.dep_ == "appos":
                out.append(("accused", child))
            if child.dep_ == "prep" and lem(child) in {"like", "of"} and person_noun:
                out += [("accused", o) for o in child.children if o.dep_ == "pobj"]
        while noun.dep_ == "conj":
            noun = noun.head
        # "call Cunningham an enforcer or a dirty player"
        if noun.dep_ in {"oprd", "ccomp", "xcomp"} and lem(noun.head) in LABEL_VERBS:
            out += [("accused", c) for c in noun.head.children if c.dep_ == "dobj"]
        # "accusations of dirty play" → who the accusations are aimed at
        for anc in list(tok.head.ancestors)[:4]:
            if lem(anc) in ACCUSATION_NOUNS:
                for c in anc.children:
                    if c.dep_ == "prep" and lem(c) in {"against", "about", "of"} and c is not tok.head.head:
                        out += [("accused", o) for o in c.children if o.dep_ == "pobj" and lem(o) not in ACT_NOUNS]
                if anc.dep_ == "pobj" and lem(anc.head) in {"against", "of", "about", "to"}:
                    verb = anc.head.head
                    out += [("accused", c) for c in verb.children if c.dep_ in {"dobj", "nsubjpass"}]
                break
        # "Carrington is a dirty player" / "she isn't a dirty player"
        if person_noun and noun.dep_ in {"attr", "acomp"}:
            subj = subject_of(noun.head)
            if subj:
                out.append(("accused", subj))
        # "description of her as a dirty player", "described her as dirty"
        if noun.dep_ == "pobj" and lem(noun.head) == "as":
            up = noun.head.head
            for sib in up.children:
                if sib.dep_ in {"dobj", "nsubjpass"}:
                    out.append(("accused", sib))
                if sib.dep_ == "prep" and lem(sib) == "of":
                    out += [("accused", o) for o in sib.children if o.dep_ == "pobj"]
        # "Clark needed an enforcer", "Clark has an enforcer": the subject is the
        # other party, not the person the word describes
        if person_noun and noun.dep_ == "dobj" and lem(noun.head) in {"need", "have", "get", "add", "sign", "want", "find", "hire"}:
            subj = subject_of(noun.head)
            if subj:
                out.append(("victim", subj))
        for child in noun.children:
            if child.dep_ == "poss":
                # "Carrington's dirty foul" → Carrington did it; but "Caitlin Clark's
                # enforcer" → Clark is the one the enforcer is *for*
                out.append(("victim" if person_noun else "accused", child))
            if child.dep_ == "prep" and lem(child) in VICTIM_PREPS:
                out += [("victim", o) for o in child.children if o.dep_ == "pobj"]
            if child.dep_ == "prep" and lem(child) in DOER_PREPS:
                out += [("accused", o) for o in child.children if o.dep_ == "pobj"]
        # "dirty play that injured Cunningham", "a dirty play, contact that left Cunningham bloodied"
        for n in [noun] + [c for c in noun.children if c.dep_ in {"appos", "conj"}]:
            for child in n.children:
                if child.dep_ in {"relcl", "acl"}:
                    out += [("victim", o) for o in child.children if o.dep_ in {"dobj", "nsubjpass"}]
        # "Carrington committed a dirty play"
        verb = noun.head
        if noun.dep_ in {"dobj", "attr"} and lem(verb) in DOER_VERBS and not person_noun:
            subj = subject_of(verb)
            if subj:
                out.append(("accused", subj))
        # "hit Cunningham with a dirty foul"
        if noun.dep_ == "pobj" and lem(noun.head) == "with":
            verb = noun.head.head
            for sib in verb.children:
                if sib.dep_ == "dobj":
                    out.append(("victim", sib))
                if sib.dep_ == "nsubj":
                    out.append(("accused", sib))
        # "Clark has been the target of hard fouls and dirty plays"
        for anc in list(noun.ancestors)[:4]:
            if lem(anc) in RECEIVER_NOUNS and anc.dep_ in {"attr", "acomp", "pobj"}:
                subj = subject_of(anc.head)
                if subj:
                    out.append(("victim", subj))
                break
        # fallback: the subject of the nearest clause, "Carrington has a history of dirty play"
        if not out and (person_noun or lem(noun) in ACT_NOUNS):
            for anc in list(noun.ancestors)[:5]:
                if anc.pos_ in {"VERB", "AUX"}:
                    subj = subject_of(anc)
                    if subj and lem(subj) not in {"it", "that", "this", "which", "what", "there"}:
                        out.append(("accused", subj))
                        break
    # "she is dirty", "she plays dirty", "did me dirty"
    elif anchor.dep_ in {"acomp", "attr", "advmod", "oprd"} and head.pos_ in {"VERB", "AUX"}:
        if lem(head) in LABEL_VERBS:
            out += [("accused", c) for c in head.children if c.dep_ == "dobj"]
        else:
            for sib in head.children:
                if sib.dep_ in {"nsubj", "nsubjpass"}:
                    # "Cunningham's playing style was ... dirty": the possessor
                    poss = [c for c in sib.children if c.dep_ == "poss"]
                    if poss:
                        out.append(("accused", poss[0]))
                    elif sib.lemma_ not in {"play", "foul", "hit", "it", "that", "this", "which", "what", "style", "game"}:
                        out.append(("accused", sib))
                if sib.dep_ == "dobj" and lem(head) == "do":
                    out.append(("victim", sib))
    # "called Carrington dirty" (parsed as ccomp/xcomp)
    elif anchor.dep_ in {"ccomp", "xcomp"} and lem(head) in LABEL_VERBS:
        out += [("accused", c) for c in head.children if c.dep_ == "dobj"]
    found = []
    for role, t in out:
        name = resolve(doc, clusters, t)
        if name:
            found.append((role, name))
    return found


def main(word, show=False):
    import spacy
    from fastcoref import FCoref
    nlp = spacy.load("en_core_web_lg")
    coref = FCoref(device="cpu")
    rx = re.compile(rf"\b{re.escape(word)}\b", re.I)

    rows = []
    for outlet, path in OUTLETS.items():
        df = pd.read_csv(path)
        df["body"] = df.body.fillna("")
        hits = df[df.body.str.contains(rx)]
        for _, r in hits.iterrows():
            rows.append((outlet, r.get("date", ""), r.get("headline", ""), r.body[:MAX_CHARS]))
    print(f"{len(rows)} articles use “{word}”", flush=True)

    texts = [body for *_, body in rows]
    preds = coref.predict(texts=texts)
    counts = defaultdict(lambda: {"Fox News": Counter(), "others": Counter()})
    unresolved = Counter()
    for (outlet, date, headline, body), pred in zip(rows, preds):
        clusters = pred.get_clusters(as_strings=False)
        doc = nlp(body)
        side = "Fox News" if outlet == "Fox News" else "others"
        for tok in doc:
            if not rx.fullmatch(tok.text):
                continue
            found = readings(doc, clusters, tok)
            if show:
                print(f"\n[{outlet} · {date}] {headline[:80]}")
                print("   " + tok.sent.text.strip()[:260])
                print("   →", found or "(no one found)")
            if not found:
                unresolved[side] += 1
            for role, name in set(found):
                counts[name][side][role] += 1

    print("  about = the person the word describes · other = the other party (the one fouled, the one protected)")
    print(f"\n{'':22}{'Fox about':>12}{'Fox other':>12}{'oth about':>13}{'oth other':>12}")
    for name, c in sorted(counts.items(), key=lambda kv: -sum(kv[1]["Fox News"].values())):
        print(f"{name:22}{c['Fox News']['accused']:>12}{c['Fox News']['victim']:>12}"
              f"{c['others']['accused']:>13}{c['others']['victim']:>12}")
    print(f"\nuses with nobody resolved: Fox {unresolved['Fox News']} · others {unresolved['others']}")

    out = HERE / "static" / "data" / "word_targets"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{word}.json").write_text(json.dumps(
        {name: {side: dict(c) for side, c in sides.items()} for name, sides in counts.items()},
        indent=1))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    main(args[0] if args else "dirty", show="--show" in sys.argv)
