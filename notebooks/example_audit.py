"""Audit the example sentences the player-words chart shows.

Notebook 09 writes .cache/audit_candidates.jsonl: the examples whose pronoun
the coreference model resolved with low confidence, every example of the
"play" relation, and the example on every word card the site shows ("card":
is this word really about her?). `prepare` splits them into batches with the question to put
to a language model; the verdicts come back as data/audit/verdict_NNN.json
([{"id", "verdict", "answer"}], verdict "right"/"wrong"/"unclear" for a
pronoun, "yes"/"no"/"unclear" for play and cards); `apply` folds them into
data/example_audit.json, which the notebook consults on its next run, and
prints the error rates.
    python3 notebooks/example_audit.py prepare [batch size]
    python3 notebooks/example_audit.py apply
"""
import json, sys
from collections import Counter, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
CACHE, AUDIT = HERE / "notebooks/.cache", HERE / "data/audit"

# what each card's tab claims about her, for the question
CARD_CLAIM = {
    "subject": "something {who} does or says (she is the one doing it)",
    "object": "something done to {who} or said about her (she is on the receiving end)",
    "describe": "a description of {who} herself",
    "play": "a description of {who}'s own play or on-court conduct",
    "all": "said about {who} herself: something she does, something done to her, or a description of her",
}

def kind_of(c):
    return c.get("kind") if c.get("kind") == "card" else ("pronoun" if c["pronoun"] else "play")

def question(c):
    who = c["player"]
    if kind_of(c) == "card":
        claim = CARD_CLAIM.get(c["relation"].rstrip("2"), CARD_CLAIM["all"]).format(who=who)
        return (f'Our chart lists the word "{c["word"]}" as {claim}, based on this passage. '
                f'Read the passage: is that right? Answer "yes" if the word is used about {who} in that way, '
                f'"no" if it is about someone or something else or is not used that way (say what it is '
                f'about instead), or "unclear" if the passage does not settle it.')
    if c["pronoun"]:
        return (f'In the passage, the word "{c["word"]}" is attached to the pronoun "{c["pronoun"]}". '
                f'Our system says that "{c["pronoun"]}" refers to {who}. Is that right? '
                f'Answer "right" if the pronoun refers to {who}, "wrong" if it refers to someone else '
                f'(say who), or "unclear" if the passage does not settle it.')
    return (f'In the passage, does the word "{c["word"]}" describe {who}\'s own basketball play or on-court '
            f'conduct (how she plays, a foul, a shot, her defense, her physicality)? Answer "yes", "no" '
            f'(say what it describes instead), or "unclear".')

def prepare(size=50):
    rows = [json.loads(l) for l in (CACHE / "audit_candidates.jsonl").read_text().splitlines() if l.strip()]
    AUDIT.mkdir(parents=True, exist_ok=True)
    for f in AUDIT.glob("batch_*.json"):
        f.unlink()
    for i in range(0, len(rows), size):
        batch = [{"id": c["id"], "kind": kind_of(c), "player": c["player"],
                  "word": c["word"], "text": c["text"], "question": question(c)} for c in rows[i:i + size]]
        (AUDIT / f"batch_{i // size:03d}.json").write_text(json.dumps(batch, ensure_ascii=False, indent=1))
    print(f"{len(rows)} candidates in {(len(rows) + size - 1) // size} batches under data/audit/")

def apply():
    rows = {c["id"]: c for c in (json.loads(l) for l in (CACHE / "audit_candidates.jsonl").read_text().splitlines() if l.strip())}
    store_path = HERE / "data/example_audit.json"   # kept in git: the charts depend on it
    store = json.loads(store_path.read_text()) if store_path.exists() else {}
    fresh = 0
    for f in sorted(AUDIT.glob("verdict_*.json")):
        for v in json.loads(f.read_text()):
            if v.get("id") in rows and v.get("verdict"):
                c = rows[v["id"]]
                store[v["id"]] = {"verdict": v["verdict"].lower(), "answer": v.get("answer", ""),
                                  "kind": kind_of(c), "player": c["player"],
                                  "outlet": c["outlet"], "relation": c["relation"], "confidence": c["confidence"]}
                fresh += 1
    store_path.write_text(json.dumps(store, ensure_ascii=False, indent=0))
    print(f"{fresh} verdicts folded in; {len(store)} on file")
    by = defaultdict(Counter)
    for v in store.values():
        by[v["kind"]][v["verdict"]] += 1
        by[f'{v["kind"]} · {v["outlet"]}'][v["verdict"]] += 1
    for k, c in sorted(by.items()):
        n = sum(c.values()); bad = c.get("wrong", 0) + c.get("no", 0)
        print(f"  {k:38s} n={n:4d}  wrong={bad:3d} ({bad / n:.0%})  unclear={c.get('unclear', 0)}")

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "prepare"
    prepare(int(sys.argv[2])) if cmd == "prepare" and len(sys.argv) > 2 else prepare() if cmd == "prepare" else apply()
