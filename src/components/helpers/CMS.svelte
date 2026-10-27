<script>
	// Renders the Doc's [body]. A chart line reads
	//   chart: name | key: value | ...
	// — the name picks a component from `components`, the labeled parts become props.
	import { tick } from "svelte";
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
		"GridWall",
		"NetworkScrolly",
		"NetworkMap",
		"NetworkScrollyOld",
		"FramingTabs",
		"FramingSwarm",
		"FightinWordsScrolly",
		"FightinWordsBarsScrolly",
		"TernaryScrolly",
		"OutletGapScrolly",
		"GapToTernaryScrolly",
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
	const NESTING = new Set(["Subsections", "Aside", "TvBeside", "SideBySide"]);
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
		"SideBySide"
	]);

	// one-liner: `chart: name | key: value | …`
	// block (scrollies): `{.chart}` with `id:` and a nested `[.steps]` array
	// {.TimelineBars} block: the type IS the component; value holds the fields
	function chartProps(value) {
		if (typeof value === "string")
			return parseChart(value ? "_ | " + value : "_").props;
		// here the type names the component, so `id` is free to pass through (GridWall uses it)
		return pairsToProps(Object.entries(value ?? {}));
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
				out.push({
					type: it.type.toLowerCase(),
					value: String(it.value ?? "").trim()
				});
			} else if (it.type === "text" && /^\s*<li[\s>]/i.test(it.value)) {
				const last = out[out.length - 1];
				if (last && /^(ul|ol)$/.test(last.type)) last.value += it.value.trim();
				else out.push({ type: "ul", value: it.value.trim() });
			} else out.push(it);
		}
		return out;
	}

	// a heading's link: "h3: The Universe" can be linked as #the-universe
	const slug = (text) =>
		String(text ?? "")
			.replace(/<[^>]*>/g, "")
			.toLowerCase()
			.replace(/&[a-z]+;/g, "")
			.replace(/[^a-z0-9]+/g, "-")
			.replace(/^-+|-+$/g, "");
	const isHeading = (b) => /^h[2-4]$/.test(b.type);

	// a section with `collapsible: true` in the Doc (under its `section:` line)
	// shows only its heading until clicked; a link to it (#methods), or to a
	// heading inside it (#the-universe), opens it.
	// `collapsible: open` folds the same way but starts open
	const foldValue = (section) =>
		String(section.collapsible ?? "")
			.trim()
			.toLowerCase();
	const foldable = (section) => ["true", "open"].includes(foldValue(section));
	const splitHeading = (section) => {
		const content = section.content ?? [];
		const i = content.findIndex((b) => b.type === "h2");
		if (i < 0) return [section.section, content];
		return [content[i].value, content.filter((_, k) => k !== i)];
	};
	let opened = $state(
		Object.fromEntries(
			body.filter((s) => foldValue(s) === "open").map((s) => [s.section, true])
		)
	);
	$effect(() => {
		const openFromLink = () => {
			const id = decodeURIComponent(location.hash.slice(1));
			if (!id) return;
			const section = body.find(
				(s) =>
					foldable(s) &&
					(s.section === id ||
						(s.content ?? []).some((b) => isHeading(b) && slug(b.value) === id))
			);
			if (!section || opened[section.section]) return;
			opened[section.section] = true;
			// once it has opened, go to the heading that was linked
			tick().then(() => document.getElementById(id)?.scrollIntoView());
		};
		openFromLink();
		addEventListener("hashchange", openFromLink);
		return () => removeEventListener("hashchange", openFromLink);
	});

	const ROTS = [-1.8, 1.4, -1.1, 1.7, -1.5, 1.2];
	const youtubeId = (url) =>
		(url.match(/(?:shorts\/|watch\?v=|youtu\.be\/|embed\/)([\w-]{6,})/) ??
			[])[1];
</script>

<!-- the blocks of a section, in order -->
{#snippet blockList(content)}
	{#each blocks(content) as b}
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
				{#if props.kicker && !SELF_CAPTIONED.has(name)}
					<p class="kicker">{@html props.kicker}</p>
				{/if}
				{#if props.subtitle && !SELF_CAPTIONED.has(name)}
					<p class="chart-subtitle">{@html props.subtitle}</p>
				{/if}
				{#if C}<C
						{name}
						{...props}
						{...NESTING.has(name) ? { components } : {}}
					/>{:else}<p class="missing">
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
			{@const maxW =
				{ small: 380, medium: 500 }[size.toLowerCase()] ??
				(parseInt(size) || null)}
			{#if /\.pdf$/i.test(src)}
				<!-- a PDF in the same block: letter.pdf | title | caption -->
				<figure class="photo pdf">
					<div class="page">
						<object
							data="{base}/images/{src}"
							type="application/pdf"
							title={alt || src}
						>
							<p class="fallback">
								<a href="{base}/images/{src}" target="_blank" rel="noopener"
									>Open {alt || src}</a
								>
							</p>
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
			<svelte:element
				this={b.type}
				id={isHeading(b) ? slug(b.value) : undefined}
				>{@html hl(clipPops(faces(b.value, base), base))}</svelte:element
			>
		{/if}
	{/each}
{/snippet}

{#each body as section, i (section.section ?? i)}
	<section class="act" class:fold={foldable(section)} id={section.section}>
		{#if foldable(section)}
			<!-- a collapsible section: its heading opens and closes the rest -->
			{@const [heading, rest] = splitHeading(section)}
			<h3 class="fold-head">
				<button
					type="button"
					aria-expanded={!!opened[section.section]}
					onclick={() => (opened[section.section] = !opened[section.section])}
					>{@html heading}<span class="chev" aria-hidden="true"></span></button
				>
			</h3>
			{#if opened[section.section]}{@render blockList(rest)}{/if}
		{:else}
			{@render blockList(section.content)}
		{/if}
	</section>
{/each}

<style>
	.act {
		margin: 56px 0;
	}
	/* the opening section starts flush with the top of the page (the intro wall) */
	.act:first-of-type {
		margin-top: 0;
	}

	p {
		width: 100%;
		max-width: 700px;
		margin: 0 auto;
	}

	#methods p, #reading p, #reading ul {
		font-family: var(--font-sans);
		font-size: 1rem;
	}

	/* a linked heading (#the-universe) lands below the section's sticky heading */
	.fold :global(:is(h2, h3, h4)[id]) {
		scroll-margin-top: 5rem;
	}
	/* a collapsible section: the heading is the button, with a chevron */
	.fold {
		display: flex;
		flex-direction: column;
		align-items: center;
		margin: 28px auto;
		max-width: 1000px;
		padding: 0 1rem;
	}
	.fold + .fold {
		margin-top: -28px;
	}
	.fold-head {
		width: 100%;
		font-weight: 700;
		margin: 0 0 1rem 0;
		height: 4.5rem;
		position: sticky;
		top: 0;
		z-index: 1000;
		background: var(--wnba-tan-bg);
		border-bottom: 1px solid var(--color-rule);
		/* while it's pinned, its background runs the full width of the screen, so
		   charts wider than the text column (Explore's) don't show past its ends */
		box-shadow: 0 0 0 100vmax var(--wnba-tan-bg);
		clip-path: inset(0 -100vmax);
	}
	.fold-head button {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 16px;
		width: 100%;
		padding: 18px 0;
		border: 0;
		background: none;
		font: inherit;
		color: inherit;
		text-align: left;
		cursor: pointer;
	}
	/* phones: the arrow keeps clear of the corner sound button (SoundCorner) */
	@media (max-width: 768px) {
		.fold-head button {
			padding-right: 3.5rem;
		}
	}
	.chev {
		flex: none;
		width: 12px;
		height: 12px;
		margin-right: 4px;
		border-right: 2.5px solid currentColor;
		border-bottom: 2.5px solid currentColor;
		transform: translateY(-3px) rotate(45deg);
		transition: transform 200ms ease;
	}
	.fold-head button[aria-expanded="true"] .chev {
		transform: translateY(3px) rotate(-135deg);
	}
	.fold-head button:focus-visible {
		outline: 2px solid var(--color-ink);
		outline-offset: 4px;
	}
	p {
		font-size: 18px;
		line-height: 1.65;
		margin-bottom: 1em;
		color: var(--color-fg);
		padding: 0 1rem;
	}
	@media(max-width: 640px) {
		p {
			font-size: 16px;
		}
	}
	.kicker {
		background: var(--wnba-red);
		color: var(--wnba-tan-bg);
		display: inline-block;
		width: auto;
		text-transform: uppercase;
		font-family: var(--font-sans);
		font-weight: 700;
		font-size: 10px;
		padding: 6px;
		margin: 0 0 6px 0;
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
		margin: 0 auto 1rem auto;
		padding-left: 1.3em;
		color: var(--color-ink);
		max-width: 700px;
	}
	ul :global(li),
	ol :global(li) {
		margin-bottom: 0.55em;
	}

	.chart {
		margin: 0;
	}
	.chart.full-bleed {
		width: 100vw;
		margin-top: 3rem;
		/* centred with margins, not a transform: a transform here would pin anything
		   position: fixed inside (GridWall's call bubble) to this box, not the screen */
		margin-left: calc(50% - 50vw);
		padding: 0;
	}
	/* ...but not the page's opening wall: with nothing above it, its margin would
	   push the whole page down */
	.act:first-of-type > .chart.full-bleed:first-child {
		margin-top: 0;
		margin-bottom: 3rem;
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
		font-size: 18px;
		font-family: var(--font-sans);
		margin: 0 0 12px;
		padding: 0;
		line-height: 1.15;
		font-weight: 700;
		color: var(--color-gray-950);
	}
	.chart-caption {
		font-size: 12px;
		font-family: var(--font-sans);
		color: var(--wnba-tan-dark);
		margin: 4px auto 3rem auto;
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
	/* desktop: larger body text; phones keep 17px */
	@media (min-width: 769px) {
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
		margin: 3rem auto;
		max-width: 700px;
		padding: 1rem;
	}
	.photo img {
		display: block;
		width: 100%;
		border-radius: 4px;
		box-shadow: 0 3px 12px rgba(0, 0, 0, 0.12);
		border: 1px solid var(--color-rule);
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
		font-size: 12px;
		font-family: var(--font-sans);
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
