# How Does Fox News Frame the WNBA?

A data-driven essay about how Fox News covers the WNBA — and how differently
everyone else does. By [Melanie Walsh](https://melaniewalsh.org).

This is the **streamlined, publishable repo**: the essay site, the data as
CSVs, and short notebooks that reproduce the headline findings. The full
research pipeline (harvesters, caches, every experiment) lives in the private
companion repo, `wnba-politics-full`.

## The site

A [SvelteKit](https://kit.svelte.dev) app built on
[The Pudding's svelte-starter](https://github.com/the-pudding/svelte-starter).

```bash
npm install
npm run dev        # local preview at localhost:5173
```

- **Prose** comes from a Google Doc (ArchieML). `npm run gdoc` pulls it into
  `src/data/copy.json`. The Doc *is* the essay, in order: a `[body]` of
  sections, each with prose, images, clippings, and charts in the flow.
- **Charts** are summoned two ways. A simple chart is one line:
  `chart: timeline-clark | nba: true | caption: …` — the name picks a
  component from the map in `Index.svelte`, the labeled parts become props.
  A scrollytelling chart is a block with its steps nested right inside it,
  at its spot in the prose:

  ```
  {.chart}
  id: ternary-scrolly

  [.steps]
  groups: viktor, bout
  text: While MSNBC named the man Griner was exchanged for, Viktor Bout…
  []
  {}
  ```
- **Components** live in `src/components/` — one file per chart, named the
  way the Doc names them. `helpers/CMS.svelte` renders the Doc's body and
  owns every chart's title and caption. Colors are CSS variables defined at
  the bottom of `Index.svelte`; edit them there (or live in dev tools on
  `<html>`) and every chart follows.
- **Chart data** lives in `src/data/` — CSV where the data is a flat table
  (`outlet_topics.csv`, `fox_ngrams.csv`, `trans_articles.csv`), JSON where
  it's nested (networks, word grids, examples). All generated from the
  corpora by the full repo's pipeline.

## The data (`data/`)

One CSV per outlet — every WNBA article we collected, with full text where
the outlet allows it:

| file | articles | text | source |
|---|---|---|---|
| `fox_wnba.csv` | ~2,200 | full text | Fox's own tag feeds |
| `fox_nba.csv` | ~10,700 | full text | Fox's NBA tag feeds (the control) |
| `espn.csv` | ~5,700 | full text | ESPN's API |
| `just_womens_sports.csv` | ~3,200 | full text | their WordPress API |
| `the_athletic.csv` | ~2,500 | headlines | sitemaps (bodies paywalled) |
| `cbs_sports.csv` | ~3,200 | headlines | Wayback crawl index |
| `usa_today.csv` | ~2,700 | headlines | Wayback crawl index |
| `all_outlets_index.csv` | ~58,000 | index only | everything, incl. Yahoo |
| `chyron_words.csv` | — | — | TV chyrons via the Internet Archive's Third Eye |

(Yahoo's full text is ~90MB and lives in the full repo / Drive.)

## The notebooks (`notebooks/`)

Short, self-contained, CSV-in → table-out. Run in order or independently:

1. **01-fightin-words** — which words Fox uses more than Just Women's Sports
   (and vice versa), by weighted log-odds. The piece's core method.
2. **02-topic-rates** — the share of each outlet's articles touching
   race/protest and LGBTQ topics, by year. The piece's comparison charts.
3. **03-chyron-ternary** — each network's most distinctive chyron words,
   including the Griner-swap example (*viktor bout* vs *merchant of death*).

```bash
pip install pandas jupyter
jupyter lab notebooks/
```
