"""Write the Fightin' Words data the site bundles, and the parts it fetches.

The pooled comparisons (all / sports / news / left / right / the pair) are what
the published piece shows, so they are all that goes into the page bundle;
headline words inline, article words and phrases in a file fetched when a
reader switches to articles. The single-outlet comparisons are an evaluation
tool: the dev server shows their pills and fetches one small file per outlet.
Stats are stored compactly as [z, n, fox, other] under one key per comparison.
"""
import json, re
from pathlib import Path
from outlets import GROUPS, COMPARISON

HERE = Path(__file__).resolve().parents[1]
SRC, STATIC = HERE / "src/data", HERE / "static/data"
# what the published page carries: the pools and the comparison outlets
POOLED = list(GROUPS) + list(COMPARISON)

def slug(label):
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")

def _row(entry, key):
    return [entry["z"][key], entry["n"][key], entry.get("nf", {}).get(key, 0), entry.get("no", {}).get(key, 0)]

def _compact(entries, keys):
    out = []
    for e in entries:
        s = {k: _row(e, k) for k in keys if k in e["z"]}
        if s:
            out.append({"word": e["word"], "s": s})
    return out

def _table(entries, key):
    return {e["word"]: _row(e, key) for e in entries if key in e["z"]}

def write_fighting_words(grid, lit):
    singles = [k for k in grid["outlets"] if k not in POOLED]
    bundle = {
        "outlets": [k for k in grid["outlets"] if k in POOLED],
        "outletsExtra": singles,                       # the dev server's pills
        "outletN": grid["outletN"],
        "words": _compact(grid["words"], POOLED),
        "hasArticles": bool(grid.get("articleWords")),
        "articleOutlets": grid["articleOutlets"],
        "articleOutletN": grid["articleOutletN"],
        "players": grid["players"],
        "byPlayer": {p: _compact(w, POOLED) for p, w in grid["byPlayer"].items()},
        "playerN": grid["playerN"],
        "note": grid["note"],
    }
    (SRC / "fighting_words.json").write_text(json.dumps({"grid": bundle, "lit": lit}, ensure_ascii=False))
    STATIC.mkdir(parents=True, exist_ok=True)
    # article words and two-word phrases load separately, each when first shown
    (STATIC / "fw_articles.json").write_text(json.dumps(_compact(grid["articleWords"], POOLED), ensure_ascii=False))
    (STATIC / "fw_bigrams.json").write_text(json.dumps(_compact(grid["articleBigrams"], POOLED), ensure_ascii=False))
    # three-word phrases (2026-09-30), when the notebook scored them
    if grid.get("articleTrigrams"):
        (STATIC / "fw_trigrams.json").write_text(json.dumps(_compact(grid["articleTrigrams"], POOLED), ensure_ascii=False))
    d = STATIC / "fw_outlet"; d.mkdir(exist_ok=True)
    for k in singles:
        (d / f"{slug(k)}.json").write_text(json.dumps({
            "headlines": _table(grid["words"], k),
            "articles": _table(grid["articleWords"], k),
            "bigrams": _table(grid["articleBigrams"], k),
            "trigrams": _table(grid.get("articleTrigrams", []), k),
            "players": {p: _table(w, k) for p, w in grid["byPlayer"].items()}}, ensure_ascii=False))
    mb = lambda p: f"{p.stat().st_size / 1e6:.1f} MB"
    print(f"fighting_words.json {mb(SRC / 'fighting_words.json')} bundled; fw_articles.json {mb(STATIC / 'fw_articles.json')}, "
          f"fw_bigrams.json {mb(STATIC / 'fw_bigrams.json')}; "
          f"{len(singles)} outlet files, {sum(f.stat().st_size for f in d.glob('*.json')) / 1e6:.1f} MB")

def write_player_words(slim):
    """`slim` is notebook 09's site payload; the per-outlet blocks leave the bundle."""
    d = STATIC / "player_outlet"; d.mkdir(parents=True, exist_ok=True)
    for who, block in slim["players"].items():
        by = block.pop("vsByOutlet", None) or {}
        # the pooled groups (sports / news / left / right) stay in the bundle as
        # the chart's group pills; the single outlets go to the player's file
        block["vsByOutlet"] = {rel: {k: v for k, v in cmp.items() if k in GROUPS} for rel, cmp in by.items()}
        singles = {rel: {k: v for k, v in cmp.items() if k not in GROUPS} for rel, cmp in by.items()}
        block["vsByOutletKeys"] = {rel: sorted(cmp) for rel, cmp in by.items()}
        if any(singles.values()):
            (d / f"{slug(who)}.json").write_text(json.dumps(singles, ensure_ascii=False))
        # two-word phrases (the relations ending in 2, 2026-09-30) would double
        # the bundle: they go to one file per player, fetched when switched on
        phr = {}
        for part in ("relations", "counts", "vsOutlets", "vsCounts", "vsByOutlet"):
            got = {rel: v for rel, v in (block.get(part) or {}).items() if rel.endswith("2")}
            for rel in got:
                block[part].pop(rel)
            if got:
                phr[part] = got
        if phr:
            dp = STATIC / "player_phrases2"; dp.mkdir(parents=True, exist_ok=True)
            (dp / f"{slug(who)}.json").write_text(json.dumps(phr, ensure_ascii=False))
    out = SRC / "player_words.json"
    out.write_text(json.dumps(slim, ensure_ascii=False))
    print(f"player_words.json {out.stat().st_size / 1e6:.1f} MB bundled; "
          f"{len(list(d.glob('*.json')))} player files, {sum(f.stat().st_size for f in d.glob('*.json')) / 1e6:.1f} MB")

if __name__ == "__main__":
    # re-split the full files a notebook wrote before this module existed
    fw = json.loads((SRC / "fighting_words.json").read_text())
    if "articleWords" in fw["grid"]:
        write_fighting_words(fw["grid"], fw["lit"])
    pw = json.loads((SRC / "player_words.json").read_text())
    if not any("vsByOutletKeys" in b for b in pw["players"].values()):
        write_player_words(pw)
