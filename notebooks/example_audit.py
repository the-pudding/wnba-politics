"""Audit the example sentences the player-words chart shows.

Notebook 09 writes .cache/audit_candidates.jsonl: the examples whose pronoun
the coreference model resolved with low confidence, and every example of the
"play" relation. `prepare` splits them into batches with the question to put
to a language model; the verdicts come back as data/audit/verdict_NNN.json
([{"id", "verdict", "answer"}], verdict "right"/"wrong"/"unclear" for a
pronoun, "yes"/"no"/"unclear" for play); `apply` folds them into
.cache/example_audit.json, which the notebook consults on its next run, and
prints the error rates.
    python3 notebooks/example_audit.py prepare [batch size]
    python3 notebooks/example_audit.py apply
"""
import json, sys
from collections import Counter, defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
CACHE, AUDIT = HERE / "notebooks/.cache", HERE / "data/audit"

def question(c):
    who = c["player"]
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
        batch = [{"id": c["id"], "kind": "pronoun" if c["pronoun"] else "play", "player": c["player"],
                  "word": c["word"], "text": c["text"], "question": question(c)} for c in rows[i:i + size]]
        (AUDIT / f"batch_{i // size:03d}.json").write_text(json.dumps(batch, ensure_ascii=False, indent=1))
    print(f"{len(rows)} candidates in {(len(rows) + size - 1) // size} batches under data/audit/")

def apply():
    rows = {c["id"]: c for c in (json.loads(l) for l in (CACHE / "audit_candidates.jsonl").read_text().splitlines() if l.strip())}
    store_path = CACHE / "example_audit.json"
    store = json.loads(store_path.read_text()) if store_path.exists() else {}
    fresh = 0
    for f in sorted(AUDIT.glob("verdict_*.json")):
        for v in json.loads(f.read_text()):
            if v.get("id") in rows and v.get("verdict"):
                c = rows[v["id"]]
                store[v["id"]] = {"verdict": v["verdict"].lower(), "answer": v.get("answer", ""),
                                  "kind": "pronoun" if c["pronoun"] else "play", "player": c["player"],
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
