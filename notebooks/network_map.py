"""Data for the network map (src/data/network_map.json, used by NetworkMap.svelte).

Starts from notebook 07's headline network, puts everyone in a group, and adds
a few more people. Run after notebook 07:

    python notebooks/network_map.py
"""
import collections, csv, json, re
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
net = json.loads((HERE / "src/data/headline_network.json").read_text())
roster = json.loads((HERE / "src/data/people.json").read_text())
rows = list(csv.DictReader((HERE / "src/data/fox_player_headlines.csv").open()))

# ---------------------------------------------------------------------------
# Edit these
# ---------------------------------------------------------------------------

# Groups: league, politics, media (commentators), antitrans, celebs.
# Players and coaches in people.json are "league" unless listed here.
GROUP = {
    # former players now on TV
    "Sheryl Swoopes": "league", "Chiney Ogwumike": "league",
    "Donald Trump": "politics", "Joe Biden": "politics", "J.D. Vance": "politics",
    "Kelly Loeffler": "politics", "Barack Obama": "politics", "Michelle Obama": "politics",
    "Kamala Harris": "politics",
    # the Griner prisoner swap
    "Paul Whelan": "politics", "Viktor Bout": "politics",
    "Jemele Hill": "media", "Stephen A. Smith": "media", "Clay Travis": "media",
    "Sunny Hostin": "media", "Charlie Kirk": "media", "Dave Portnoy": "media",
    "Riley Gaines": "antitrans", "Enes Kanter Freedom": "antitrans", "J.K. Rowling": "antitrans",
    "LeBron James": "celebs", "Megan Rapinoe": "celebs", "Taylor Swift": "celebs", "Morgan Wallen": "celebs",
}

# People added beyond notebook 07's network: group, and a regex for their
# name in headlines (None = use the pattern in people.json).
# Photos go in static/net/<first-last>.jpg or .png.
EXTRA = {
    "Kim Mulkey": ("league", None),
    "Adam Silver": ("league", None),
    "Kelsey Mitchell": ("league", None),
    "Hailey Van Lith": ("league", r"van lith"),
    "Liz Cambage": ("league", r"cambage"),
    "Elena Delle Donne": ("league", r"delle donne"),
    "Lisa Leslie": ("league", r"lisa leslie"),
    "Azzi Fudd": ("league", r"azzi fudd|\bfudd\b"),
    "Bobby Burack": ("media", r"burack"),
    "Dan Dakich": ("media", r"dakich"),
    "Pat McAfee": ("media", r"mcafee"),
    "Charles Barkley": ("media", r"charles barkley|(?<!saquon )\bbarkley\b"),
    "Nancy Lieberman": ("media", r"nancy lieberman|\blieberman\b"),
    "Monica McNutt": ("media", r"mcnutt"),
    "Steph Curry": ("celebs", r"steph(?:en)? curry"),
    "Tom Brady": ("celebs", r"tom brady"),
    "Antonio Brown": ("celebs", r"antonio brown"),
}

# photos that are wide headshots (they sit a little differently in the circle)
HEADSHOT = {"caitlin-clark", "angel-reese", "brittney-griner", "sophie-cunningham", "paige-bueckers",
            "dijonai-carrington", "natasha-cloud", "a-ja-wilson", "sue-bird", "layshia-clarendon", "cameron-brink"}

# ---------------------------------------------------------------------------


def group_of(node):
    if node["name"] in GROUP:
        return GROUP[node["name"]]
    if node["group"] in ("players", "league"):
        return "league"
    raise ValueError(f"no group for {node['name']}: add them to GROUP")


def face_of(name):
    if roster.get(name, {}).get("face"):
        return roster[name]["face"]
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    for ext in ("png", "jpg"):
        if (HERE / "static/net" / f"{slug}.{ext}").exists():
            return f"{slug}.{ext}"
    return None


# every month in range, so the timeline has no gaps
first, last = net["months"][0], net["months"][-1]
months, (y, m) = [], map(int, first.split("-"))
while True:
    months.append(f"{y}-{m:02d}")
    if months[-1] >= last:
        break
    m, y = (1, y + 1) if m == 12 else (m + 1, y)
rows = [r for r in rows if first <= r["date"][:7] <= last]

nodes = []


def add(name, group, heads, monthly):
    nodes.append({
        "name": name, "group": group, "face": face_of(name),
        "headshot": roster.get(name, {}).get("slug") in HEADSHOT,
        "monthly": monthly, "heads": heads,
    })


for n in net["nodes"]:
    heads = sorted(([h["d"], h["t"]] for h in n["headlines"]), reverse=True)
    add(n["name"], group_of(n), heads, net["solo_monthly"][n["name"]])

# the added people, matched in headlines the way notebook 07 matches the roster
on_map = {n["name"] for n in nodes}
extra_rx = {name: re.compile(roster[name]["rx"] if pat is None else pat, re.I)
            for name, (group, pat) in EXTRA.items() if name not in on_map}
for name, rx in extra_rx.items():
    heads = sorted(([r["date"], r["title"]] for r in rows if rx.search(r["title"])), reverse=True)
    add(name, EXTRA[name][0], heads, dict(sorted(collections.Counter(d[:7] for d, _ in heads).items())))

# lines: notebook 07's, plus the added people with anyone in the same headline
index = {n["name"]: i for i, n in enumerate(nodes)}
edges = [[index[a], index[b], month, k] for month, lst in net["edges_monthly"].items() for a, b, k in lst]
everyone = {**{name: re.compile(roster[name]["rx"], re.I) for name in on_map}, **extra_rx}
shared = collections.Counter()
for r in rows:
    here = [name for name, rx in everyone.items() if rx.search(r["title"])]
    for i, a in enumerate(here):
        for b in here[i + 1:]:
            if a in extra_rx or b in extra_rx:
                shared[(a, b, r["date"][:7])] += 1
edges += [[index[a], index[b], month, k] for (a, b, month), k in shared.items()]

total = collections.Counter(r["date"][:7] for r in rows)
out = {
    "months": months,
    "total": {m: total.get(m, 0) for m in months},
    "inRange": len(rows),
    # OutKick's own site, and its sections on foxnews.com since the move there
    "outkick": sum(1 for r in rows if re.search(r"outkick\.com|foxnews\.com/outkick-", r["url"])),
    "nodes": nodes,
    "edges": edges,
}
(HERE / "src/data/network_map.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
print(f"{len(nodes)} people ({len(extra_rx)} added), {len(edges)} month-pairs, {len(rows)} headlines")
