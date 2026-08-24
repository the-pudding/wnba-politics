<script>
	// Renders the Doc's [body]. A chart line reads
	//   chart: name | key: value | ...
	// — the name picks a component from `components`, the labeled parts become props.
	import { base } from "$app/paths";
	import FoxBadge from "$components/FoxBadge.svelte";

	let { body = [], components = {} } = $props();

	// scrollytelling charts take the full viewport width
	const FULL_BLEED = new Set(["NetworkScrolly", "FightinWordsScrolly", "TernaryScrolly",
		"OutletGapScrolly", "TimelineDotsScrolly", "FightinWordsVerbsAdj",
		// legacy Doc ids
		"network-story", "fightin-words-scrolly", "ternary-scrolly",
		"outlet-gap-scrolly", "timeline-scrolly", "player-words-scrolly"]);
	// these draw their own title and caption
	const SELF_CAPTIONED = new Set(["TimelineDotsScrolly", "HeadlineTable",
		"timeline-scrolly", "headline-table"]);

	const PALETTE = { green: "#1f9d6e", pink: "#d55181", purple: "#b04ac2",
		teal: "#17a2b8", violet: "#7a6bcc", blue: "#2a78d6", orange: "#eda100" };
	const CLIP_BLUE = "#003366";
	// ==word== -> tinted highlight
	const hl = (html, color = "#d55181") => (html ?? "").replace(/==(.+?)==/g,
		(_, w) => `<mark style="background:${color}2e; box-shadow: inset 0 -2px 0 ${color}66">${w}</mark>`);

	// one-liner: `chart: name | key: value | …`
	// block (scrollies): `{.chart}` with `id:` and a nested `[.steps]` array
	function parseChart(value) {
		let name, pairs;
		if (typeof value === "string") {
			const [first, ...parts] = value.split("|").map((s) => s.trim());
			name = first;
			pairs = parts
				.map((p) => p.match(/^(\w+)\s*:\s*([^]*)$/) ?? (p ? [null, "words", p] : null))
				.filter(Boolean)
				.map((m) => [m[1], m[2]]);
		} else {
			name = value.id;
			pairs = Object.entries(value).filter(([k]) => k !== "id");
		}
		const props = {};
		for (const [key, v] of pairs) {
			if (key === "steps") props.steps = Array.isArray(v) ? v : [];
			else if (key === "words") props.words = v.split(",").map((w) => w.trim());
			else if (key === "groups") props.groups = v.split("/")
				.map((g) => g.split(",").map((w) => w.trim()).filter(Boolean)).filter((g) => g.length);
			else if (key === "from") props.from = /^\d{4}$/.test(v) ? v + "-01" : v;
			else if (key === "to") props.to = /^\d{4}$/.test(v) ? v + "-12" : v;
			else props[key] = v === "true" ? true : v === "false" ? false : v;
		}
		return { name, props };
	}

	// clip: tag | date | color | title   (color optional)
	function parseClip(v) {
		const p = v.split("|").map((s) => s.trim());
		if (p.length >= 4 && (PALETTE[p[2]] || /^#/.test(p[2])))
			return { tag: p[0], date: p[1], title: p.slice(3).join(" | ") };
		if (p.length >= 3) return { tag: p[0], date: p[1], title: p.slice(2).join(" | ") };
		if (p.length === 2) return { date: p[0], title: p[1] };
		return { title: v };
	}

	// consecutive clips group into one tilted stack
	function blocks(content) {
		const out = [];
		for (const it of content ?? []) {
			if (!it?.value) continue;
			if (it.type === "clip") {
				const last = out[out.length - 1];
				if (last?.clips) last.clips.push(parseClip(it.value));
				else out.push({ type: "clips", clips: [parseClip(it.value)] });
			} else out.push(it);
		}
		return out;
	}

	const ROTS = [-1.8, 1.4, -1.1, 1.7, -1.5, 1.2];
	const youtubeId = (url) =>
		(url.match(/(?:shorts\/|watch\?v=|youtu\.be\/|embed\/)([\w-]{6,})/) ?? [])[1];
</script>

{#each body as section, i (section.section ?? i)}
	<section class="act" id={section.section}>
		{#each blocks(section.content) as b}
			{#if b.type === "text"}
				<p>{@html hl(b.value)}</p>
			{:else if b.type === "chart"}
				{@const { name, props } = parseChart(b.value)}
				{@const C = components[name]}
				<div class="chart" class:full-bleed={FULL_BLEED.has(name)}>
					{#if props.title && !SELF_CAPTIONED.has(name)}
						<h4 class="chart-title">{@html hl(props.title)}</h4>
					{/if}
					{#if C}<C {name} {...props} />{:else}<p class="missing">Unknown chart: “{name}”</p>{/if}
					{#if props.caption && !SELF_CAPTIONED.has(name)}
						<p class="chart-caption">{@html props.caption}</p>
					{/if}
				</div>
			{:else if b.type === "clips"}
				<div class="clips">
					{#each b.clips as c, j}
						<div class="clip" style="--rot: {ROTS[j % ROTS.length]}deg">
							<FoxBadge />
							{#if c.date}<span class="clip-date">{c.date}</span>{/if}
							<p class="clip-title">{@html hl(c.title, CLIP_BLUE)}</p>
						</div>
					{/each}
				</div>
			{:else if b.type === "img"}
				{@const [src, alt = "", caption = ""] = b.value.split("|").map((s) => s.trim())}
				<figure class="photo">
					<img src="{base}/images/{src}" {alt} loading="lazy" />
					{#if caption}<figcaption>{@html caption}</figcaption>{/if}
				</figure>
			{:else if /^embed$/i.test(b.type)}
				{@const [url, caption = ""] = b.value.split("|").map((s) => s.trim())}
				{@const id = youtubeId(url)}
				{#if id}
					<figure class="embed" class:portrait={/\/shorts\//.test(url)}>
						<div class="frame">
							<iframe src="https://www.youtube-nocookie.com/embed/{id}"
								title={caption || "Embedded video"} loading="lazy"
								allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
								referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
						</div>
						{#if caption}<figcaption>{@html caption}</figcaption>{/if}
					</figure>
				{/if}
			{:else}
				<svelte:element this={b.type}>{@html hl(b.value)}</svelte:element>
			{/if}
		{/each}
	</section>
{/each}

<style>
	.act { margin: 56px 0; }
	p { font-size: 17px; line-height: 1.65; margin-bottom: 1em; color: var(--color-ink); }
	p :global(mark) { color: inherit; padding: 0 3px; border-radius: 2px; }

	.chart { margin: 12px 0 22px; }
	.chart.full-bleed {
		width: 100vw;
		margin-left: 50%;
		transform: translateX(-50%);
		padding: 0 12px;
	}
	.chart-title { font-size: 19px; text-align: center; margin: 0 0 10px; color: var(--color-ink); }
	.chart-caption { font-size: 12.5px; color: rgba(42, 21, 3, 0.6); margin-top: 4px; text-align: center; }
	.missing { font-size: 13px; color: #a33; }

	.clips { display: flex; flex-direction: column; gap: 12px; max-width: 560px; margin: 6px auto 26px; }
	.clip {
		background: var(--color-paper);
		border: 1px solid #e6dcc3;
		box-shadow: 0 3px 12px rgba(0, 0, 0, 0.12);
		padding: 10px 15px;
		transform: rotate(var(--rot, 0deg));
	}
	.clip-title { font-size: 15.5px; font-weight: 700; line-height: 1.4; margin: 5px 0 0; font-family: Georgia, serif; color: #1a1a1a; }
	.clip-date { font-size: 12px; color: rgba(42, 21, 3, 0.55); }

	.photo { margin: 18px auto 26px; max-width: 640px; }
	.photo img {
		display: block;
		width: 100%;
		border-radius: 8px;
		box-shadow: 0 4px 18px rgba(0, 0, 0, 0.18);
		border: 1px solid rgba(42, 21, 3, 0.15);
	}
	.photo figcaption { font-size: 12.5px; color: rgba(42, 21, 3, 0.6); margin-top: 6px; text-align: center; }

	.embed { margin: 20px auto; max-width: 620px; }
	.embed.portrait { max-width: 330px; }
	.embed .frame {
		position: relative; width: 100%; padding-top: 56.25%;
		background: rgba(42, 21, 3, 0.12); border-radius: 4px; overflow: hidden;
	}
	.embed.portrait .frame { padding-top: 177.8%; }
	.embed iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; }
	.embed figcaption {
		font-size: 12.5px; line-height: 1.5; color: rgba(42, 21, 3, 0.62);
		text-align: center; margin-top: 7px;
	}
</style>
