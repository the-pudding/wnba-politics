"""A random check of the player-word counts, behind the charts' scores and totals.

Notebook 09 writes .cache/counted.json: every word it counted for a player, and
the sentence each count came from. `sample` draws counts at random (a word
counted 300 times is 300 times as likely to be drawn as one counted once) and
writes them in batches for a reviewer, with the same questions as the cards
(example_audit.py). `apply` folds the verdicts into data/example_audit.json,
where notebook 09 takes the wrong ones off its counts on its next run, and
prints the error rate with a 95% interval.

    python3 notebooks/sample_audit.py sample [n] [draw]   # draw 1, 2, …: a fresh sample each
    python3 notebooks/sample_audit.py apply
"""
import hashlib, json, math, random, sys
from collections import Counter, defaultdict
from pathlib import Path

from example_audit import CARD_CLAIM

HERE = Path(__file__).resolve().parents[1]
CACHE, AUDIT = HERE / "notebooks/.cache", HERE / "data/audit"
STORE = HERE / "data/example_audit.json"
SEED = 2026      # the same draws every time (draw 2 adds 1, and so on)
BATCH = 125      # counts per reviewer batch


def shown_word(relation, lemma):
    # "play" keys carry the act and the verb after the word: "physical|play|"
    return lemma.split("|")[0] if relation.startswith("play") else lemma


def question(row):
    who = row["player"]
    claim = CARD_CLAIM.get(row["relation"].rstrip("2"), CARD_CLAIM["all"]).format(who=who)
    return (f'Our chart counts the word "{row["word"]}" as {claim}, based on this passage. The word '
            f'may appear in another form ("scored" for "score"); "not-" means it is negated. '
            f'Read the passage: is that right? Answer "yes" if the word is used about {who} in that way, '
            f'"no" if it is about someone or something else or is not used that way (say what it is '
            f'about instead), or "unclear" if the passage does not settle it.')


def sample(n=500, draw=1):
    counted = json.loads((CACHE / "counted.json").read_text())
    texts = {}
    for name in ("fox_parsed", "others_parsed"):
        texts.update(json.loads((CACHE / f"{name}.json").read_text())["sentences"])
    pool, weights = [], []
    for side, sources in counted.items():
        for key, by_source in sources.items():
            for source, count in by_source.items():
                pool.append((side, key, source))
                weights.append(count)
    rng = random.Random(SEED + draw - 1)
    rows, seen = [], set()
    for side, key, source in rng.choices(pool, weights, k=n * 3):
        who, relation, lemma = key.split("|", 2)
        sent, outlet, era = source.split("|")
        if (key, sent) in seen or sent not in texts:
            continue
        seen.add((key, sent))
        row = {"id": hashlib.md5(f"sample|{key}|{sent}".encode()).hexdigest()[:16], "kind": "card", "draw": draw,
               "player": who, "relation": relation, "word": shown_word(relation, lemma),
               "key": key, "sent": sent, "side": side, "outlet": outlet, "text": texts[sent]}
        row["question"] = question(row)
        rows.append(row)
        if len(rows) == n:
            break
    AUDIT.mkdir(parents=True, exist_ok=True)
    for f in AUDIT.glob("sample_batch_*.json"):
        f.unlink()
    for i in range(0, len(rows), BATCH):
        (AUDIT / f"sample_batch_{i // BATCH:03d}.json").write_text(
            json.dumps(rows[i:i + BATCH], ensure_ascii=False, indent=1))
    print(f"{len(rows)} counts drawn from {sum(weights):,} into {math.ceil(len(rows) / BATCH)} batches under data/audit/")


def interval(bad, n, z=1.96):
    # Wilson score interval for a proportion
    if not n:
        return 0, 0
    p = bad / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0, centre - half), min(1, centre + half)


def apply():
    rows = {r["id"]: r for f in sorted(AUDIT.glob("sample_batch_*.json")) for r in json.loads(f.read_text())}
    store = json.loads(STORE.read_text()) if STORE.exists() else {}
    by = defaultdict(Counter)
    for f in sorted(AUDIT.glob("sample_verdict_*.json")):
        for v in json.loads(f.read_text()):
            r = rows.get(v.get("id"))
            if not r or not v.get("verdict"):
                continue
            verdict = v["verdict"].lower()
            store[v["id"]] = {"verdict": verdict, "answer": v.get("answer", ""), "kind": "sample", "draw": r.get("draw", 1),
                              "player": r["player"], "outlet": r["outlet"], "relation": r["relation"],
                              "key": r["key"], "sent": r["sent"]}
            for label in ("all", r["side"], r["relation"].rstrip("2")):
                by[label][verdict] += 1
    STORE.write_text(json.dumps(store, ensure_ascii=False, indent=0))
    for label, c in sorted(by.items(), key=lambda kv: kv[0] != "all"):
        n = sum(c.values()); bad = c.get("no", 0)
        lo, hi = interval(bad, n)
        print(f"  {label:14s} n={n:4d}  wrong={bad:3d} ({bad / n:.1%}, 95% interval {lo:.1%}–{hi:.1%})  unclear={c.get('unclear', 0)}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sample"
    if cmd == "sample":
        sample(*(int(a) for a in sys.argv[2:4]))
    else:
        apply()
