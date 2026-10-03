<script>
	// Renders the Doc's [body]. A chart line reads
	//   chart: name | key: value | ...
	// — the name picks a component from `components`, the labeled parts become props.
	import { base } from "$app/paths";
	import FoxBadge from "$components/FoxBadge.svelte";
	import FaceRow from "$components/FaceRow.svelte";
	import {
		PALETTE,
		CLIP_BLUE,
		hl,
		parseClip,
		faces,
		clipPops
	} from "$utils/clips.js";

	let { body = [], components = {} } = $props();

	// scrollytelling charts take the full viewport width
	const FULL_BLEED = new Set([
		"NetworkScrolly",
		"NetworkMap",
		"NetworkScrollyOld",
		"FightinWordsScrolly",
		"FightinWordsBarsScrolly",
		"TernaryScrolly",
		"OutletGapScrolly",
		"FightinWordsVerbsAdj",
		"FightinWordsBars",
		// legacy Doc ids
		"network-story",
		"fightin-words-scrolly",
		"ternary-scrolly",
		"outlet-gap-scrolly",
		"timeline-scrolly",
		"player-words-scrolly",
		"TvSet"
	]);
	// these render Doc copy of their own and need the component map for it
	const NESTING = new Set(["Subsections", "Aside", "TvBeside"]);
	// these draw their own title and caption
	const SELF_CAPTIONED = new Set([
		"Subsections",
		"FoxVsField",
		"ShareBars",
		// the Fightin' Words charts fill in their own caption's {slots}
		"FightinWordsBarsScrolly",
		"FightinWordsBars",
		"Aside",
		"BoxScore",
		"SimpleBars",
		"HeadlineTable",
		"timeline-scrolly",
		"headline-table",
		"Gallery",
		"HeadlineGallery",
		"TvSet",
		"TvBeside",
		"WordCompare",
		"WordNeighbors",
	]);

	// one-liner: `chart: name | key: value | …`
	// block (scrollies): `{.chart}` with `id:` and a nested `[.steps]` array
	// {.TimelineBars} block: the type IS the component; value holds the fields
	function chartProps(value) {
		if (typeof value === "string")
			return parseChart(value ? "_ | " + value : "_").props;
		const pairs = Object.entries(value ?? {}).filter(([k]) => k !== "id");
		return pairsToProps(pairs);
	}

	function parseChart(value) {
		let name, pairs;
		if (typeof value === "string") {
			const [first, ...parts] = value.split("|").map((s) => s.trim());
			name = first;
			pairs = parts
				.map(
					(p) =>
						p.match(/^(\w+)\s*:\s*([^]*)$/) ?? (p ? [null, "words", p] : null)
				)
				.filter(Boolean)
				.map((m) => [m[1], m[2]]);
		} else {
			name = value.id;
			pairs = Object.entries(value).filter(([k]) => k !== "id");
		}
		return { name, props: pairsToProps(pairs) };
	}

	function pairsToProps(pairs) {
		const props = {};
		for (const [key, v] of pairs) {
			if (key === "steps" || key === "rows")
				props[key] = Array.isArray(v) ? v : [];
			else if (key === "words") props.words = v.split(",").map((w) => w.trim());
			else if (key === "groups")
				props.groups = v
					.split("/")
					.map((g) =>
						g
							.split(",")
							.map((w) => w.trim())
							.filter(Boolean)
					)
					.filter((g) => g.length);
			else if (key === "from") props.from = /^\d{4}$/.test(v) ? v + "-01" : v;
			else if (key === "to") props.to = /^\d{4}$/.test(v) ? v + "-12" : v;
			else props[key] = v === "true" ? true : v === "false" ? false : v;
		}
		return props;
	}

	// consecutive clips group into one tilted stack
	function blocks(content) {
		const out = [];
		for (const it of content ?? []) {
			const isList = /^(ul|ol)$/i.test(it?.type ?? "");
			if (!it?.value && !isList) continue;
			if (it.type === "clip") {
				const last = out[out.length - 1];
				if (last?.clips) last.clips.push(parseClip(it.value));
				else out.push({ type: "clips", clips: [parseClip(it.value)] });
			} else if (isList) {
				// "ul:" in the Doc opens a list; the <li> lines that follow are
				// its items (the parser hands each line over as its own text)
				out.push({ type: it.type.toLowerCase(), value: String(it.value ?? "").trim() });
			} else if (it.type === "text" && /^\s*<li[\s>]/i.test(it.value)) {
				const last = out[out.length - 1];
				if (last && /^(ul|ol)$/.test(last.type)) last.value += it.value.trim();
				else out.push({ type: "ul", value: it.value.trim() });
			} else out.push(it);
		}
		return out;
	}

	const ROTS = [-1.8, 1.4, -1.1, 1.7, -1.5, 1.2];
	const youtubeId = (url) =>
		(url.match(/(?:shorts\/|watch\?v=|youtu\.be\/|embed\/)([\w-]{6,})/) ??
			[])[1];
</script>

{#each body as section, i (section.section ?? i)}
	<section class="act" id={section.section}>
		{#each blocks(section.content) as b}
			{#if b.type === "text"}
				<p>{@html hl(clipPops(faces(b.value, base), base))}</p>
			{:else if b.type === "chart" || components[b.type]}
				{@const { name, props } =
					b.type === "chart"
						? parseChart(b.value)
						: { name: b.type, props: chartProps(b.value) }}
				{@const C = components[name]}
				<div class="chart" class:full-bleed={FULL_BLEED.has(name)}>
					{#if props.title && !SELF_CAPTIONED.has(name)}
						<h4 class="chart-title">{@html hl(props.title)}</h4>
					{/if}
					<!-- subtitle: a plain line under the title, in the ink colour -->
					{#if props.subtitle && !SELF_CAPTIONED.has(name)}
						<p class="chart-subtitle">{@html props.subtitle}</p>
					{/if}
					{#if C}<C {name} {...props} {...(NESTING.has(name) ? { components } : {})} />{:else}<p class="missing">
							Unknown chart: “{name}”
						</p>{/if}
					{#if props.caption && !SELF_CAPTIONED.has(name)}
						<p class="chart-caption">{@html props.caption}</p>
					{/if}
				</div>
			{:else if b.type === "faces"}
				{@const [names, flag = ""] = b.value.split("|").map((s) => s.trim())}
				<FaceRow {names} plain={/^plain$/i.test(flag)} />
			{:else if b.type === "clips"}
				<div class="clips">
					{#each b.clips as c, j}
						<div class="clip" style="--rot: {ROTS[j % ROTS.length]}deg">
							<FoxBadge />
							{#if c.date}<span class="clip-date">{c.date}</span>{/if}
							<p class="clip-title">
								{@html hl(faces(c.title, base), CLIP_BLUE)}
							</p>
						</div>
					{/each}
				</div>
			{:else if b.type === "img"}
				<!-- file | alt | caption | size (optional: small, medium, or a width
				     in px) -->
				{@const [src, alt = "", caption = "", size = ""] = b.value
					.split("|")
					.map((s) => s.trim())}
				{@const maxW = { small: 380, medium: 500 }[size.toLowerCase()] ?? (parseInt(size) || null)}
				{#if /\.pdf$/i.test(src)}
					<!-- a PDF in the same block: letter.pdf | title | caption -->
					<figure class="photo pdf">
						<div class="page">
							<object data="{base}/images/{src}" type="application/pdf" title={alt || src}>
								<p class="fallback"><a href="{base}/images/{src}" target="_blank" rel="noopener">Open {alt || src}</a></p>
							</object>
						</div>
						{#if caption}<figcaption>{@html caption}</figcaption>{/if}
					</figure>
				{:else}
					<figure class="photo" style:max-width={maxW ? `${maxW}px` : null}>
						<img src="{base}/images/{src}" {alt} loading="lazy" />
						{#if caption}<figcaption>{@html caption}</figcaption>{/if}
					</figure>
				{/if}
			{:else if /^(quote|blockquote|pullquote)$/i.test(b.type)}
				<!-- quote: the words | who said it, where -->
				{@const [words, who = ""] = String(b.value)
					.split(/\s\|\s/)
					.map((s) => s.trim())}
				<blockquote class="quote">
					<p>{@html hl(clipPops(faces(words, base), base))}</p>
					{#if who}<cite>{@html who}</cite>{/if}
				</blockquote>
			{:else if /^embed$/i.test(b.type)}
				{@const [url, caption = ""] = b.value.split("|").map((s) => s.trim())}
				{@const id = youtubeId(url)}
				{#if id}
					<figure class="embed" class:portrait={/\/shorts\//.test(url)}>
						<div class="frame">
							<iframe
								src="https://www.youtube-nocookie.com/embed/{id}"
								title={caption || "Embedded video"}
								loading="lazy"
								allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
								referrerpolicy="strict-origin-when-cross-origin"
								allowfullscreen
							></iframe>
						</div>
						{#if caption}<figcaption>{@html caption}</figcaption>{/if}
					</figure>
				{/if}
			{:else}
				<svelte:element this={b.type}
					>{@html hl(clipPops(faces(b.value, base), base))}</svelte:element
				>
			{/if}
		{/each}
	</section>
{/each}

<style>
	.act {
		margin: 56px 0;
	}
	p {
		font-size: 17px;
		line-height: 1.65;
		margin-bottom: 1em;
		color: var(--color-ink);
	}
	p :global(mark) {
		color: inherit;
		padding: 0 3px;
		border-radius: 2px;
	}
	/* a Doc list ("ul:" then <li> lines) reads like the paragraphs */
	ul,
	ol {
		font-size: 17px;
		line-height: 1.65;
		margin: 0 0 1em;
		padding-left: 1.3em;
		color: var(--color-ink);
	}
	ul :global(li),
	ol :global(li) {
		margin-bottom: 0.55em;
	}

	.chart {
		margin: 12px 0 22px;
	}
	.chart.full-bleed {
		width: 100vw;
		margin-left: 50%;
		transform: translateX(-50%);
		padding: 0 12px;
	}
	.chart-title {
		font-size: 19px;
		text-align: center;
		margin: 0 0 10px;
		color: var(--color-ink);
	}
	.chart-title + .chart-subtitle {
		margin-top: -6px;
	}
	.chart-subtitle {
		font-size: 15px;
		text-align: center;
		margin: 0 0 12px;
		color: var(--color-ink);
	}
	.chart-caption {
		font-size: 12.5px;
		color: rgba(42, 21, 3, 0.6);
		margin-top: 4px;
		text-align: center;
	}
	.missing {
		font-size: 13px;
		color: #a33;
	}

	.clips {
		display: flex;
		flex-direction: column;
		gap: 12px;
		max-width: 560px;
		margin: 6px auto 26px;
	}
	.clip {
		background: var(--color-paper);
		border: 1px solid var(--color-rule);
		box-shadow: 0 3px 12px rgba(0, 0, 0, 0.12);
		padding: 10px 15px;
		transform: rotate(var(--rot, 0deg));
	}
	.clip-title {
		font-size: 15.5px;
		font-weight: 700;
		line-height: 1.4;
		margin: 5px 0 0;
		font-family: var(--font-serif);
		color: var(--color-ink-dark);
	}
	.clip-date {
		font-size: 12px;
		color: rgba(42, 21, 3, 0.55);
	}

	/* quote: … | … — a pull quote with the Fox red bar the cards use */
	.quote {
		margin: 18px auto 24px;
		max-width: 560px;
		padding: 2px 0 2px 18px;
		border-left: 4px solid var(--color-fox);
	}
	.quote p {
		font-size: 17px;
		line-height: 1.65;
		font-style: italic;
		margin: 0;
		color: var(--color-ink);
	}
	/* desktop: larger body text (2026-09-30); phones keep 17px */
	@media (min-width: 769px) {
		p,
		ul,
		ol,
		.quote p {
			font-size: 19px;
			line-height: 1.6;
		}
	}
	.quote cite {
		display: block;
		margin-top: 10px;
		font-family: var(--font-chart);
		font-style: normal;
		font-size: 12.5px;
		letter-spacing: 0.02em;
		color: rgba(42, 21, 3, 0.65);
	}
	.quote cite::before {
		content: "— ";
	}

	.photo {
		margin: 18px auto 26px;
		max-width: 640px;
	}
	.photo img {
		display: block;
		width: 100%;
		border-radius: 8px;
		box-shadow: 0 4px 18px rgba(0, 0, 0, 0.18);
		border: 1px solid rgba(42, 21, 3, 0.15);
	}
	/* a PDF: a letter-shaped frame the document scrolls inside */
	.photo.pdf .page {
		position: relative;
		width: 100%;
		padding-top: 129%;
		border-radius: 8px;
		overflow: hidden;
		box-shadow: 0 4px 18px rgba(0, 0, 0, 0.18);
		border: 1px solid rgba(42, 21, 3, 0.15);
		background: #fff;
	}
	.photo.pdf object {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
	}
	.photo.pdf .fallback {
		padding: 24px;
		text-align: center;
	}
	.photo figcaption {
		font-size: 12.5px;
		color: rgba(42, 21, 3, 0.6);
		margin-top: 6px;
		text-align: center;
	}

	.embed {
		margin: 20px auto;
		max-width: 620px;
	}
	.embed.portrait {
		max-width: 330px;
	}
	.embed .frame {
		position: relative;
		width: 100%;
		padding-top: 56.25%;
		background: rgba(42, 21, 3, 0.12);
		border-radius: 4px;
		overflow: hidden;
	}
	.embed.portrait .frame {
		padding-top: 177.8%;
	}
	.embed iframe {
		position: absolute;
		inset: 0;
		width: 100%;
		height: 100%;
		border: 0;
	}
	.embed figcaption {
		font-size: 12.5px;
		line-height: 1.5;
		color: rgba(42, 21, 3, 0.62);
		text-align: center;
		margin-top: 7px;
	}
</style>
