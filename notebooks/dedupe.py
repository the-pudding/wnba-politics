"""One copy of each article.

The harvests reached some articles more than once, and found 947 extra copies
in ESPN alone: the same story under a second URL (a #b or ?utm tail, :80, a
re-slugged ESPN or AP link with the same id, a CBS News station page for each
local affiliate), the web and print (ProQuest) versions of one story, and a
wire story's later rewrites. Each copy counted as another article everywhere.

Rows are the same article when any of these match:
  1. the URL, once tails, ports, query strings and slugs are set aside
     (ESPN /id/N, AP's 32-character id, USA Today's numeric id, a CBS News
     station page's slug)
  2. the whole text, compared on letters and digits only. This also folds
     templated pages into one: USA Today's 241 "Where to watch X vs Y" TV
     listings carry one season-preview text, and AP's "Today in Sports" items
     repeat one text under different headlines; counted apiece, that text
     would weigh in hundreds of times.
  3. the opening 300 characters of text, for dates at most 3 days apart, when
     at least half of the two texts' five-word runs are shared: a wire story's
     rewrite, a print version. A series intro ("The MVP Case For…", a mock
     draft's) shares the opening and little else; page furniture ("Let
     friends in your social network know…" at USA Today) spans months.
  4. the headline and date, when one of the two has no text (headlines of
     at least six words, so "WNBA Capsules" is never matched)
  5. a print record (ProQuest) and a web article dated at most 4 days before
     it to 1 day after: the print edition rewrites the headline and edits the
     text, so rules 2 and 3 miss it. The same story when half of the first
     300 words' four-word runs are shared, or a quarter of them and at least
     35% of the names in the first 150 words (wire game recaps share stock
     phrases; two different games share few names). This catches the Post's
     and the Times' print twins.

The copy kept: the one with text, then a web page over a ProQuest record,
then a clean URL, then the longest text.

    from dedupe import dedupe
    keep, dropped = dedupe(rows)   # dropped: [(row, "duplicate of <url>")]
"""
import re
from datetime import date

SPAN = 3
OPENING = 300


def url_key(url):
    u = (url or "").strip().lower()
    u = re.sub(r"(%0a|%09|\s)+$", "", u)
    u = re.sub(r"^https?://(www\.)?", "", u)
    u = re.sub(r":\d+/", "/", u, count=1)
    u = re.split(r"#|%23|\?|%3f", u)[0].rstrip("/")
    u = re.sub(r"/amp$", "", u)
    if m := re.search(r"espn\.com/.*/id/(\d+)", u):
        return f"espn:{m.group(1)}"
    if m := re.search(r"apnews\.com/.*-([0-9a-f]{32})$", u):
        return f"ap:{m.group(1)}"
    if m := re.search(r"usatoday\.com/.*/(\d{8,10})$", u):
        return f"usat:{m.group(1)}"
    if m := re.search(r"cbsnews\.com/[a-z]+/news/([^/]+)$", u):
        return f"cbsnews:{m.group(1)}"
    return u


def _norm(text):
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def _day(d):
    try:
        return date.fromisoformat((d or "")[:10])
    except ValueError:
        return None


def _shingles(text, k=5):
    w = text.split()
    return {" ".join(w[i:i + k]) for i in range(max(1, len(w) - k + 1))}


def _similar(a, b, floor=0.5):
    sa, sb = _shingles(a), _shingles(b)
    return len(sa & sb) / max(1, min(len(sa), len(sb))) >= floor


_NOT_NAMES = {"The", "She", "They", "But", "And", "With", "After", "When", "That", "This", "WNBA",
              "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}


def _names(text):
    first = " ".join((text or "").split()[:150])
    return set(re.findall(r"\b[A-Z][a-z]{2,}(?:['’][a-z]+)?\b", first)) - _NOT_NAMES


def _print_twin(p, w):
    a = _shingles(" ".join(_norm(p["body"]).split()[:300]), 4)
    b = _shingles(" ".join(_norm(w["body"]).split()[:300]), 4)
    runs = len(a & b) / max(1, min(len(a), len(b)))
    if runs >= 0.5:
        return True
    if runs < 0.25:
        return False
    na, nb = _names(p["body"]), _names(w["body"])
    return len(na & nb) / max(1, len(na | nb)) >= 0.35


def _rank(row):
    body = row.get("body") or ""
    url = row.get("url") or ""
    clean = not re.search(r"#|%23|%3f|\?|%0a|%09|:\d+/", url.lower())
    return (len(body.split()) > 80, "proquest.com" not in url, clean, len(body))


def dedupe(rows):
    n = len(rows)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def join(ids):
        for j in ids[1:]:
            a, b = find(ids[0]), find(j)
            if a != b:
                parent[b] = a

    by_url, by_text, by_open, by_head = {}, {}, {}, {}
    for i, r in enumerate(rows):
        by_url.setdefault(url_key(r.get("url")), []).append(i)
        body = r.get("body") or ""
        if len(body.split()) > 80:
            t = _norm(body)
            by_text.setdefault(t, []).append(i)
            by_open.setdefault(t[:OPENING], []).append(i)
        head = _norm(r.get("headline"))
        if len(head.split()) >= 6:
            by_head.setdefault((head, (r.get("date") or "")[:10]), []).append(i)

    for ids in by_url.values():
        if len(ids) > 1:
            join(ids)
    for ids in by_text.values():
        if len(ids) > 1:
            join(ids)
    for ids in by_open.values():
        if len(ids) < 2:
            continue
        for x, i in enumerate(ids):
            for j in ids[x + 1:]:
                di, dj = _day(rows[i].get("date")), _day(rows[j].get("date"))
                if di and dj and abs((di - dj).days) <= SPAN and \
                        _similar(_norm(rows[i]["body"]), _norm(rows[j]["body"])):
                    join([i, j])
    for ids in by_head.values():
        if len(ids) > 1 and any(len((rows[i].get("body") or "").split()) <= 80 for i in ids):
            join(ids)
    web_by_day = {}
    for i, r in enumerate(rows):
        if "proquest.com" not in (r.get("url") or "") and len((r.get("body") or "").split()) > 80:
            web_by_day.setdefault((r.get("date") or "")[:10], []).append(i)
    if web_by_day:
        from datetime import timedelta
        for i, r in enumerate(rows):
            d = _day(r.get("date"))
            if not d or "proquest.com" not in (r.get("url") or "") or len((r.get("body") or "").split()) <= 80:
                continue
            for k in range(-4, 2):
                for j in web_by_day.get(str(d + timedelta(days=k)), []):
                    if _print_twin(r, rows[j]):
                        join([j, i])

    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    keep_ids, dropped = set(), []
    for ids in groups.values():
        best = max(ids, key=lambda i: _rank(rows[i]))
        keep_ids.add(best)
        for i in ids:
            if i != best:
                dropped.append((rows[i], f"duplicate of {rows[best].get('url', '')}"))
    return [rows[i] for i in range(n) if i in keep_ids], dropped
