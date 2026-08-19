"""Pull the Google Doc, apply the edits made here since the last export, and
write both copy.json and the Doc text back out.

The Doc is the source of truth for PROSE — anything written there wins. This
only re-applies structural changes made in the repo that the Doc hasn't seen
yet (a chart swapped, a chart removed), and flags anything that looks broken.

    python merge_gdoc.py
"""
import json, re, subprocess
from datetime import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from paths import HERE
DOC_ID = "19tHhCoKdouiIrlk_KsiCwPAji-_7JSPr2c89iFt8cOQ"
RAW = HERE / "gdoc_raw.txt"
OUT_TEXT = HERE / "gdoc_full.txt"
COPY = HERE / "src" / "data" / "copy.json"

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]


def outlet_gap_caption():
    """The dot plot's caption, with its window and totals read off the data."""
    data = json.loads((HERE / "viz" / "src" / "data" / "outlet_gap.json").read_text())
    window = data.get("window", {})

    def month(stamp):
        year, mon = stamp[:4], int(stamp[5:7])
        return f"{MONTHS[mon - 1]} {year}"

    totals = data.get("totals", {})
    named = ["Fox News", "Yahoo Sports", "ESPN", "CBS Sports", "USA Today"]
    counts = ", ".join(f"{o} ({totals[o]:,})" for o in named if o in totals)
    return (f"outlet-gap | title: Who Fox covers, and who the sports press covers | caption: Each "
            f"player's share of that outlet's WNBA headlines, {month(window.get('from', '0000-00'))} "
            f"to {month(window.get('to', '0000-00'))} — the window every archive covers. A + in the "
            f"margin means Fox covers her more than the sports press does. Headlines counted: "
            f"{counts}.")


# charts retired here; if the Doc still has them, swap or drop
CHART_SWAPS = {
    "sentiment-faces": "framing-tabs | title: How Fox frames each player | caption: Four measures of "
                       "the same cast — tone, politicization, appearance and celebrity treatment. "
                       "Fox News headlines, WNBA players only. Source: Fox News.",
    "politicized": None,
    "appearance-faces": None,
    "player-volume": outlet_gap_caption(),
}
# Clippings added here that the Doc hasn't seen yet. Keyed by the sentence they
# follow, and skipped if that clip is already present, so re-running is safe.
# Nothing is force-fed into the Doc any more.
#
# These two tables existed to push new charts and paragraphs into a Doc that
# hadn't caught up yet. The Doc has since been brought level — it carries all 16
# clippings and all 12 charts itself — so every entry had become a no-op that
# fired only when a paragraph was DELETED, which meant the merge kept
# resurrecting prose that had been cut on purpose. Deleting in the Doc is now the
# way to delete.
#
# To stage something new: add it here, merge, paste the result into the Doc, then
# empty the entry again.
INSERT_BEFORE = {}
INSERT_AFTER = {
    # STAGED: stays here until the Doc carries `chart: toc` itself. Removing it
    # before then deletes the contents list from the site on the next merge.
    "So I decided to collect some data": ["chart: toc"],
}

# prose that belongs with a swapped-in chart, inserted before and after it
CHART_CONTEXT = {
    "outlet-gap": {
        "before": "But volume alone doesn't prove much — everyone covers Caitlin Clark, because she is "
                  "the biggest story women's basketball has ever had. The real question is whether Fox "
                  "covers a <em>different</em> WNBA than the sports press does. Here is each player's "
                  "share of Fox's WNBA headlines, next to her share of Yahoo Sports' and ESPN's.",
        "after": [
            "Everyone covers Clark heavily — she is <strong>38%</strong> of Yahoo's and ESPN's WNBA "
            "headlines — but Fox goes further: <strong>53%</strong>, more than half of everything it "
            "publishes about the league.",
            "And the rest of the league splits in two. Fox writes about Megan Rapinoe <strong>13×</strong> "
            "more than the sports press does, Natasha Cloud <strong>6×</strong> more, Sue Bird "
            "<strong>4×</strong> more, Brittney Griner <strong>4×</strong> more — the outspoken, the "
            "queer, the political. It writes about the league's rising stars far <em>less</em>: Aliyah "
            "Boston and Napheesa Collier at <strong>0.2×</strong>, Paige Bueckers <strong>0.4×</strong>. "
            "Even A'ja Wilson — a four-time MVP, the best player in the league — gets <strong>less</strong> "
            "of Fox's attention than she gets from Yahoo and ESPN. Fox isn't covering the WNBA more than "
            "everyone else. It's covering a different WNBA.",
        ],
    },
}


def fetch():
    url = f"https://docs.google.com/document/d/{DOC_ID}/export?format=txt"
    subprocess.run(["curl", "-sL", "--max-time", "60", "-o", str(RAW), url], check=True)
    text = RAW.read_text().lstrip("\ufeff")

    # gdoc_raw.txt is overwritten every run, so a bad edit — or a bad merge —
    # used to be unrecoverable the moment the next pull happened. These
    # snapshots cost nothing and mean the author's words can always be got back.
    history = HERE / "data" / "doc-history"
    history.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    (history / f"gdoc-{stamp}.txt").write_text(text)
    for old in sorted(history.glob("gdoc-*.txt"))[:-20]:
        old.unlink()
    return text


def parse(text):
    node = HERE / "viz"
    script = ("const a=require('archieml');const fs=require('fs');"
              "process.stdout.write(JSON.stringify(a.load(fs.readFileSync(process.argv[1],'utf8'))));")
    done = subprocess.run(["node", "-e", script, str(RAW)], cwd=node,
                          capture_output=True, text=True, check=True)
    return json.loads(done.stdout)


def apply_swaps(copy):
    swapped, dropped = [], []
    for section in copy.get("body", []):
        content = section.get("content", [])
        out = []
        for item in content:
            if item.get("type") != "chart":
                out.append(item)
                continue
            name = item["value"].split("|")[0].strip()
            if name not in CHART_SWAPS:
                out.append(item)
                continue
            replacement = CHART_SWAPS[name]
            if replacement is None:
                dropped.append(name)
                continue
            new_name = replacement.split("|")[0].strip()
            context = CHART_CONTEXT.get(new_name, {})
            if context.get("before"):
                out.append({"type": "text", "value": context["before"]})
            out.append({"type": "chart", "value": replacement})
            for paragraph in context.get("after", []):
                # an "after" entry may itself be a chart, not just prose
                if paragraph.startswith("chart: "):
                    out.append({"type": "chart", "value": paragraph[len("chart: "):]})
                else:
                    out.append({"type": "text", "value": paragraph})
            swapped.append(f"{name} -> {new_name}")
        section["content"] = out
    return swapped, dropped


# Ratios quoted in the prose ("Fox writes about Megan Rapinoe 13× more") drift
# every time the corpus grows. Rather than keep a hand-list of old-and-new pairs,
# this reads the current ratio for each player and rewrites whatever number the
# Doc has next to her name.
RATIO_NEAR_NAME = re.compile(r"(?P<name>[A-Z][\w.'’]+(?: [A-Z][\w.'’]+)+)"
                             r"(?P<gap>[^<]{0,40})<strong>(?P<value>[\d.]+)×</strong>")


def current_ratios():
    data = json.loads((HERE / "viz" / "src" / "data" / "outlet_gap.json").read_text())
    out = {}
    for person in data.get("people", []):
        ratio = person.get("ratio")
        if ratio:
            out[person["name"]] = f"{round(ratio)}" if ratio >= 10 else f"{ratio:.1f}".rstrip("0").rstrip(".")
    return out


def apply_figure_fixes(copy):
    """Refresh the ×-ratios quoted beside a player's name."""
    ratios = current_ratios()
    fixed = []

    def rewrite(match):
        fresh = ratios.get(match.group("name"))
        if not fresh or fresh == match.group("value"):
            return match.group(0)
        fixed.append(f"{match.group('value')}× -> {fresh}×  ({match.group('name')})")
        return f"{match.group('name')}{match.group('gap')}<strong>{fresh}×</strong>"

    for section in copy.get("body", []):
        for item in section.get("content", []):
            if item.get("type") == "text":
                item["value"] = RATIO_NEAR_NAME.sub(rewrite, item["value"])
    return fixed


def _unused_apply_figure_fixes(copy):
    """Swap stale numbers in place, leaving the Doc's sentences alone."""
    fixed = []
    for section in copy.get("body", []):
        for item in section.get("content", []):
            if item.get("type") != "text":
                continue
            for old, new in FIGURE_FIXES:
                if old != new and old in item["value"]:
                    item["value"] = item["value"].replace(old, new)
                    fixed.append(f"{old.split('<strong>')[-1].rstrip('</strong>')} -> "
                                 f"{new.split('<strong>')[-1].rstrip('</strong>')}"
                                 f"  ({old.split(' <strong>')[0][-24:]})")
    return fixed


# Straight substring corrections, for typos rather than recomputed figures.
# These live here rather than in the Doc so a re-pull doesn't undo them.
FRAGMENT_FIXES = [
    # the Abby Phillip piece ran 11 July 2026, not 2027
    ("race | July 2027 |", "race | July 2026 |"),
]


# The Doc carries the same chart twice, in two different arguments. The first
# instance belongs to the protest section and the second to the LGBTQ one, so
# they are rewritten by position rather than by find-and-replace.
ORDERED_CHART_FIXES = {

    "timeline-politics": [
        "timeline-protest | years: 2020-2023 | title: What Fox's WNBA coverage was about | "
        "caption: Share of Fox WNBA articles each month touching protest politics and race, "
        "2020–2023. Hover a band for an example sentence.",
        "timeline-lgbtq | years: 2020-2023 | title: And then, LGBTQ coverage | "
        "caption: Share of Fox WNBA articles each month touching LGBTQ topics and sexuality, "
        "2020–2023. Hover a band for an example sentence.",
    ],
}


def apply_ordered_chart_fixes(copy):
    seen = {}
    changed = []
    for section in copy.get("body", []):
        for item in section.get("content", []):
            if item.get("type") != "chart":
                continue
            name = item["value"].split("|")[0].strip()
            if name not in ORDERED_CHART_FIXES:
                continue
            replacements = ORDERED_CHART_FIXES[name]
            nth = seen.get(name, 0)
            if nth < len(replacements):
                item["value"] = replacements[nth]
                changed.append(f"{name} #{nth + 1} -> {replacements[nth].split('|')[0].strip()}")
            seen[name] = nth + 1
    return changed


# A bare URL on its own line parses as an ArchieML key, so the Doc's NPR link
# was rendering as a <https> element. The file is downloaded to static/images so
# the piece doesn't hotlink someone else's CDN.
REMOTE_IMAGES = {
    "//npr.brightspotcdn.com": "img: wnba-blm-2020.jpg | Minnesota Lynx players standing with linked "
                               "arms, wearing “Say Her Name” shirts | Minnesota Lynx players wear "
                               "“Say Her Name” shirts and lock arms during a moment of silence in "
                               "honor of Breonna Taylor before a game in July 2020. "
                               "Phelan M. Ebenhack/AP",
}


# Sentences that have moved into a chart. The scrollytelling word plot uses the
# Doc's own two sentences as its beats, so leaving them in the body prints them
# twice — once on the chart, once underneath it.
# Prose this script generated that the author has cut. It lives in the Doc
# because a merged copy carrying it got pasted back, so deleting it in the Doc is
# the real fix — this list is the safety net for the next time an old copy is
# pasted, and every entry is here because it was explicitly asked for.
MOVED_INTO_CHARTS = [
    "Case in point: Fox News has consistently discussed",
    "They also invoked race and racism more than other outlets",
    "CNN and MSNBC named the man Griner was exchanged for",
    "Four ways of asking the same question",
    "Kelsey Plum</strong> tops the celebrity measure",
    "Kelsey Plum tops the celebrity measure",
    "The last one is the sharpest",
    "One more thing. The trans issue was there the whole time",
    "Almost nothing before 2023. A brief spike",
    "On television it’s starker. Of the three networks",
    "This isn’t a national conversation about women’s sports",
]


def drop_moved_text(copy):
    dropped = []
    for section in copy.get("body", []):
        keep = []
        for item in section.get("content", []):
            value = item.get("value") or ""
            if item.get("type") == "text" and any(m in value for m in MOVED_INTO_CHARTS):
                dropped.append(value[:52])
                continue
            keep.append(item)
        section["content"] = keep
    return dropped


def apply_remote_images(copy):
    fixed = []
    for section in copy.get("body", []):
        for item in section.get("content", []):
            for needle, replacement in REMOTE_IMAGES.items():
                if needle in (item.get("value") or ""):
                    item["type"] = "img"
                    item["value"] = replacement[len("img: "):]
                    fixed.append(needle)
    return fixed


# Step arrays the scrollytelling charts read from the Doc. Added if the Doc
# doesn't already carry them, so the words live in the Doc and not in the
# component, where they can't be edited.
# No default step text lives here any more.
#
# STEP_ARRAYS used to hold a fallback copy of every scrolly's words, injected
# when the Doc didn't have them. That was right once, when the arrays were new.
# It stopped being right the moment the Doc carried them: hand over a merged
# file, get an edit back, and any array that went briefly missing came back in
# MY wording instead of the author's. The Doc owns these words. If an array is
# absent the chart falls back to the constants in its own component, and that is
# a bug to fix in the Doc, not something to paper over here.
STEP_ARRAYS = {}

# Nothing here may replace an array the Doc already has.
#
# A one-time STEP_RESTORES lived here to put back two beats this script had
# overwritten. It did its job and then kept doing it — silently reverting every
# later edit to the same array. A "temporary" rule that runs on every merge is
# just a rule. If an array needs restoring, do it once by hand and delete it.
def restore_steps(copy):
    return []


# which chart reads which array
STEP_OWNERS = {
    "timeline-scrolly": "transSteps",
    "outlet-gap-scrolly": "dotSteps",
    "ternary-scrolly": "swapSteps",
    "word-quadrant-scrolly": "wordSteps",
    # these two already read their arrays by default; naming them in the chart
    # line is what tells a reader of the Doc that the words are theirs to edit
    "chyron-ternary": "ternarySteps",
    "network-story": "networkSteps",
}


# The Doc labels two different sections `methods`. The first is the trans
# movement, so it gets the name it should have had; the second keeps `methods`.
# Keyed by (name, which occurrence).
SECTION_RENAMES = {("methods", 1): "trans"}


def promote_stray_headings(copy):
    """A heading written above [.+content] becomes a section property, not content.

    ArchieML reads `h2: …` before the content array as metadata on the section,
    so the heading silently disappears from the page. Move it to the top of the
    content where it belongs, at h2 to match the other sections.
    """
    moved = []
    for section in copy.get("body", []):
        # ArchieML keys are case-sensitive, so `H2:` and `h2:` are different
        # keys — and a capitalised one silently became section metadata
        keys = [k for k in list(section) if k.lower() in ("h2", "h3", "h4")]
        for key in keys:
            heading = section.pop(key, None)
            if not heading:
                continue
            content = section.setdefault("content", [])
            if any(item.get("value") == heading for item in content):
                continue
            content.insert(0, {"type": "h2", "value": heading})
            moved.append(f"{key}: {heading}")
    return moved


def rename_sections(copy):
    seen, renamed = {}, []
    for section in copy.get("body", []):
        name = section.get("section")
        if not name:
            continue
        seen[name] = seen.get(name, 0) + 1
        fresh = SECTION_RENAMES.get((name, seen[name]))
        if fresh:
            section["section"] = fresh
            renamed.append(f"{name} #{seen[name]} -> {fresh}")
    return renamed


def unique_section_names(copy):
    """Two sections can't share a name.

    The page keys its sections on `section:`, so a duplicate name — easy to
    create when pasting one section's copy under another — throws
    each_key_duplicate and renders nothing at all. Renaming is safer than
    letting the whole piece go blank.
    """
    seen, renamed = {}, []
    for section in copy.get("body", []):
        name = section.get("section")
        if not name:
            continue
        if name in seen:
            seen[name] += 1
            fresh = f"{name}-{seen[name]}"
            section["section"] = fresh
            renamed.append(f"{name} -> {fresh}")
        else:
            seen[name] = 1
    return renamed


def apply_step_arrays(copy):
    """Give each scrolly chart its steps, and put the steps in the Doc."""
    added = []
    for key, steps in STEP_ARRAYS.items():
        if not copy.get(key):
            copy[key] = steps
            added.append(key)
    for section in copy.get("body", []):
        for item in section.get("content", []):
            if item.get("type") != "chart":
                continue
            name = item["value"].split("|")[0].strip()
            key = STEP_OWNERS.get(name)
            if key and "steps:" not in item["value"]:
                item["value"] = f"{item['value'].rstrip()} | steps: {key}"
                added.append(f"{name} -> steps: {key}")
    return added


def apply_step_fixes(copy):
    """The network walk-through opens on 2023 rather than 2020."""
    steps = copy.get("networkSteps") or []
    if steps and steps[0].get("year") == "2020":
        steps[0]["year"] = "2023"
        return ["networkSteps: first beat 2020 -> 2023"]
    return []


SMART_ATTR = re.compile(r'(\s(?:href|target|rel|class)=)[“”]([^“”\'"]*)[“”]')


def straighten_attributes(copy):
    """Curly quotes in HTML attributes, which Docs inserts silently."""
    fixed = []
    for section in copy.get("body", []):
        for item in section.get("content", []):
            value = item.get("value") or ""
            if not SMART_ATTR.search(value):
                continue
            item["value"] = SMART_ATTR.sub(r'\1"\2"', value)
            fixed.append(value[:46])
    return fixed


def apply_fragment_fixes(copy):
    fixed = []
    for section in copy.get("body", []):
        for item in section.get("content", []):
            for old, new in FRAGMENT_FIXES:
                if old in (item.get("value") or ""):
                    item["value"] = item["value"].replace(old, new)
                    fixed.append(f"{old} -> {new}")
    return fixed


# Chart lines whose caption is generated from the data rather than typed. Keyed
# by exact chart name (a substring match here once ate "outlet-gap-scrolly").
TEXT_UPDATES = [
    ("chart: outlet-gap", "chart: " + outlet_gap_caption()),
    ("chart: framing-tabs",
     "chart: framing-tabs | title: How Fox frames each player"),
]


def apply_text_updates(copy):
    """Refresh figures that have been recomputed since the Doc was written."""
    changed = []
    for section in copy.get("body", []):
        for item in section.get("content", []):
            marker = "chart: " if item.get("type") == "chart" else ""
            value = marker + item.get("value", "")
            for fragment, replacement in TEXT_UPDATES:
                if fragment.startswith("chart: "):
                    # exact chart name, or "outlet-gap" swallows "outlet-gap-scrolly"
                    if item.get("type") != "chart":
                        continue
                    if item["value"].split("|")[0].strip() != fragment[len("chart: "):]:
                        continue
                elif fragment not in value:
                    continue
                if replacement.lstrip("chart: ") == item.get("value"):
                    continue
                if replacement.startswith("chart: "):
                    item["value"] = replacement[len("chart: "):]
                else:
                    item["value"] = replacement
                changed.append(fragment[:44])
    return changed


def apply_inserts(copy):
    """Add clippings around the sentence they illustrate, once.

    INSERT_BEFORE exists because an anchor is sometimes itself an inserted item,
    and this pass walks the list once — so anchoring after something that hasn't
    been added yet silently does nothing.
    """
    added = 0
    for section in copy.get("body", []):
        content = section.get("content", [])
        existing = {item.get("value", "") for item in content}
        out = []
        for item in content:
            for anchor, clips in INSERT_BEFORE.items():
                if anchor not in item.get("value", ""):
                    continue
                for clip in clips:
                    kind, _, value = clip.partition(": ")
                    if value in existing:
                        continue
                    out.append({"type": kind, "value": value})
                    added += 1
            out.append(item)
            if item.get("type") not in {"text", "h2", "h3", "chart"}:
                continue
            for anchor, clips in INSERT_AFTER.items():
                if anchor not in item.get("value", ""):
                    continue
                for clip in clips:
                    kind, _, value = clip.partition(": ")
                    if value in existing:
                        continue
                    out.append({"type": kind, "value": value})
                    added += 1
        section["content"] = out
    return added


def find_damage(copy):
    """Half-finished edits: a sentence spliced into another mid-word."""
    suspicious = []
    for section in copy.get("body", []):
        for item in section.get("content", []):
            value = item.get("value", "")
            if item.get("type") != "text":
                continue
            if re.search(r"\s{2,}\w+ \w+ (exactly|precisely),", value) or " the  " in value:
                suspicious.append((section.get("section"), value))
    return suspicious


def serialize(copy):
    lines = ["{meta}"]
    for key, value in (copy.get("meta") or {}).items():
        lines.append(f"{key}: {value}")
    lines += ["{}", "", "[body]", ""]
    for section in copy.get("body", []):
        lines += [f"section: {section.get('section','')}", ""]
        lines.append("[.+content]")
        for item in section.get("content", []):
            kind, value = item.get("type"), item.get("value", "")
            lines += [value if kind == "text" else f"{kind}: {value}", ""]
        lines += ["[]", ""]
    lines.append("[]")
    for key, value in copy.items():
        if key in {"meta", "body"} or not isinstance(value, list):
            continue
        lines += ["", f"[{key}]"]
        for item in value:
            for field, field_value in item.items():
                lines.append(f"{field}: {field_value}")
            lines.append("")
        lines.append("[]")
    return "\n".join(lines).rstrip() + "\n"


def report_active_rules():
    """Say, every run, what this script is allowed to change.

    Three separate times a rule meant to be temporary kept quietly rewriting the
    author's words. The fix is not more care — it is that nothing this script
    does to the Doc should be invisible.
    """
    rules = [
        ("adds prose", INSERT_BEFORE, INSERT_AFTER),
        ("deletes prose", MOVED_INTO_CHARTS),
        ("rewrites charts", ORDERED_CHART_FIXES, TEXT_UPDATES),
        ("rewrites text", FRAGMENT_FIXES, REMOTE_IMAGES),
        ("renames sections", SECTION_RENAMES),
        ("names step arrays", STEP_OWNERS),
    ]
    live = [(label, sum(len(t) for t in tables))
            for label, *tables in rules if sum(len(t) for t in tables)]
    if live:
        print("this merge may: " + " · ".join(f"{label} ({n})" for label, n in live))


def main():
    fetch()
    copy = parse(RAW.read_text())
    report_active_rules()
    print(f"pulled: {len(copy.get('body', []))} sections, "
          f"{sum(len(s.get('content', [])) for s in copy.get('body', []))} items")

    for fix in apply_figure_fixes(copy):
        print(f"  figure: {fix}")
    for fragment in apply_text_updates(copy):
        print(f"  refreshed figures: “{fragment}…”")
    for fix in apply_fragment_fixes(copy):
        print(f"  corrected: {fix}")
    for line in straighten_attributes(copy):
        print(f"  straightened quotes in an attribute: “{line}…”")
    for line in drop_moved_text(copy):
        print(f"  moved into the chart: “{line}…”")
    for fix in apply_remote_images(copy):
        print(f"  image: {fix} -> local file")
    for fix in apply_ordered_chart_fixes(copy):
        print(f"  chart: {fix}")
    for fix in promote_stray_headings(copy):
        print(f"  heading moved into the section: {fix}")
    for fix in rename_sections(copy):
        print(f"  section: {fix}")
    for fix in unique_section_names(copy):
        print(f"  duplicate section renamed: {fix}")
    for fix in restore_steps(copy):
        print(f"  restored: {fix}")
    for fix in apply_step_arrays(copy):
        print(f"  steps: {fix}")
    for fix in apply_step_fixes(copy):
        print(f"  {fix}")

    # swaps first: an insert may be anchored to a chart's new name
    swapped, dropped = apply_swaps(copy)
    for line in swapped:
        print(f"  swapped chart: {line}")
    for name in dropped:
        print(f"  dropped chart: {name}")

    added = apply_inserts(copy)
    if added:
        print(f"  added {added} clippings")

    for section, value in find_damage(copy):
        print(f"\n  ⚠ looks like a half-finished edit in [{section}]:\n    {value[:160]}")

    COPY.write_text(json.dumps(copy, indent=2))
    OUT_TEXT.write_text(serialize(copy))
    print(f"\nwrote {COPY.name} and {OUT_TEXT.name}")


if __name__ == "__main__":
    main()
