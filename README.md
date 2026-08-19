# How Does Fox News Frame the WNBA?

A data-driven essay about how Fox News covers the WNBA — and how differently
everyone else does. By [Melanie Walsh](https://melaniewalsh.org).

This is the **streamlined, publishable repo**: the essay site, the data as
CSVs, and short notebooks that reproduce the headline findings. The full
research pipeline (harvesters, caches, every experiment) lives in the private
companion repo, `wnba-politics-full`.

## The site

A [SvelteKit](https://kit.svelte.dev/) app built on
[The Pudding's svelte-starter](https://github.com/the-pudding/svelte-starter),
using [ArchieML](http://archieml.org/) for a micro-CMS powered by Google Docs.

### Development

```bash
npm install
npm run dev
```

### Google Doc

The copy lives in a Google Doc whose id is set in `google.config.js`. Running
`npm run gdoc` at any point (even in a new tab while the server is running)
fetches the latest Doc into `src/data/copy.json`. The Doc is the essay, in
order: a `[body]` of sections holding text, images, clippings, and charts in
the flow.

A simple chart is one line — `chart: timeline-clark | nba: true | caption: …`
— where the name picks a component from the map in `Index.svelte` and the
labeled parts become props. A scrollytelling chart is a block with its steps
nested right inside it, at its spot in the copy:

```
{.chart}
id: ternary-scrolly

[.steps]
groups: viktor, bout
text: While MSNBC named the man Griner was exchanged for, Viktor Bout…
[]
{}
```

### Components

One file per chart in `src/components/`, named the way the Doc names them.
`helpers/CMS.svelte` renders the Doc's body and owns every chart's title and
caption. Colors are CSS variables defined at the bottom of `Index.svelte`;
edit them there (or live in dev tools on `<html>`) and every chart follows.

### Embedding data

Chart data is embedded with normal import syntax (e.g.
`import rows from "$data/outlet_topics.csv"`) — CSV where the data is a flat
table (`outlet_topics.csv`, `fox_ngrams.csv`, `trans_articles.csv`), JSON
where it's nested (networks, word grids, examples). All generated from the
corpora by the full repo's pipeline.

### Style

There are a few stylesheets included by default in `src/styles`. Refer to
them in `app.css`, the place for applying global styles.

For variable parity in both CSS and JS, modify files in the `properties`
folder using the [Style Dictionary](https://amzn.github.io/style-dictionary/)
API. Run `npm run style` to regenerate the style dictionary.

Some css utility classes in `reset.css`:

- `.sr-only`: makes content invisible available for screen reader
- `.text-outline`: adds a psuedo stroke to text element

The chart palette is separate: CSS variables at the bottom of
`Index.svelte`.

#### Custom Fonts

For locally hosted fonts, simply add the font to the `static/assets` folder
and include a reference in `src/styles/font.css`, making sure the url starts
with `"assets/..."`. (This piece currently preloads The Pudding's hosted
fonts in `src/routes/+page.svelte`.)

### Deploy

```bash
npm run build
```

This generates a directory called `build` with the statically rendered app.
Pushing to `main` builds and deploys it to GitHub Pages automatically.

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
