# How Does Fox News Frame the WNBA?

A data-driven essay about how Fox News covers the WNBA — and how differently
everyone else does. 



## The site

A [SvelteKit](https://kit.svelte.dev/) app built on
[The Pudding's svelte-starter](https://github.com/the-pudding/svelte-starter),
using [ArchieML](http://archieml.org/) for a micro-CMS powered by Google Docs.

### Development

```bash
npm install
npm run dev
```

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

1. **01-fightin-words** — which words Fox uses more than Just Women's Sports
   (and vice versa), by weighted log-odds. 
2. **02-topic-rates** — the share of each outlet's articles touching
   race/protest and LGBTQ topics, by year.
3. **03-chyron-ternary** — each network's most distinctive chyron words,
   including the Griner-swap example (*viktor bout* vs *merchant of death*).

```bash
pip install pandas jupyter
jupyter lab notebooks/
```
