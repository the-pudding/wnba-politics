<script>
	// Mini-CMS for freeform Doc blocks (kids-book-animals pattern): ordinary
	// paragraphs render as <p>; a "clip:" line renders a headline clipping right
	// where it appears; consecutive clips group into one tilted stack.
	//   clip: tag | date | title
	//   clip: tag | date | color | title      (color: green pink purple teal violet blue orange)
	//   img: filename | alt text | caption(optional)   (file lives in static/images/)
	// ==word== anywhere (paragraphs, clip titles) renders as a highlighted word.
	// Any other "key: value" line renders as that HTML element (h3:, blockquote:, …).
	import { base } from "$app/paths";
	import FoxBadge from "$components/FoxBadge.svelte";
	import TimelineStatic from "$components/TimelineStatic.svelte";
	import NetworkScrolly from "$components/NetworkScrolly.svelte";
	import HeadlineTable from "$components/HeadlineTable.svelte";
	import FramingTabs from "$components/FramingTabs.svelte";
	import OutletGap from "$components/OutletGap.svelte";
	import PlayerWordsScrolly from "$components/PlayerWordsScrolly.svelte";
	import WordQuadrant from "$components/WordQuadrant.svelte";
	import TernaryStatic from "$components/TernaryStatic.svelte";
	import WordQuadrantScrolly from "$components/WordQuadrantScrolly.svelte";
	import TernaryScrolly from "$components/TernaryScrolly.svelte";
	import OutletGapScrolly from "$components/OutletGapScrolly.svelte";
	import TimelineScrolly from "$components/TimelineScrolly.svelte";
	import NgramChart from "$components/NgramChart.svelte";
	import OutletTopicCompare from "$components/OutletTopicCompare.svelte";
	import Toc from "$components/Toc.svelte";
	import copyAll from "$data/copy.json";
	let { items = [] } = $props();

	// chart: <name> — renders a chart inline at this position. Optional labeled
	// parts after pipes: words: (timeline-words), years: (e.g. 2020-2023), title:, caption:
	//   chart: timeline-words | words: anthem, kneel | title: The anthem beat | caption: Source: Fox News
	// A bare unlabeled part is treated as the words list.
	// timeline-* charts are all one component; the name selects which layers show
	const TIMELINE_CHARTS = new Set(["timeline-clark", "timeline-griner"]);
	// older aliases, kept so existing Doc lines keep working
	const CHART_ALIASES = { "timeline-zoom": "timeline-full", "timeline-chyrons": "chyron-months" };
	const NETWORK_SOURCES = { "network-story": "headline" };
	// scrollytelling embeds need the full viewport width
	const FULL_BLEED = new Set(["chyron-ternary", "chyron-words", "network-story",
		"word-quadrant-scrolly", "ternary-scrolly", "outlet-gap-scrolly", "timeline-scrolly",
		"player-words-scrolly"]);
	// dense charts that read badly squeezed into the prose column
	const WIDE = new Set([]);
	// these draw their own title and caption inside the sticky frame, so Prose
	// must not draw a second copy
	const SELF_CAPTIONED = new Set(["timeline-scrolly"]);

	const PALETTE = {
		green: "#1f9d6e", pink: "#d55181", purple: "#b04ac2", teal: "#17a2b8",
		violet: "#7a6bcc", blue: "#2a78d6", orange: "#eda100"
	};
	// ==text== -> tinted highlight. Clippings tint in the same navy as the source
	// badge, so a headline reads as one object rather than a headline plus a
	// colour-coded label of our own.
	const CLIP_BLUE = "#003366";
	const hl = (html, color = "#d55181") =>
		(html ?? "").replace(/==(.+?)==/g,
			(_, w) => `<mark style="background:${color}2e; box-shadow: inset 0 -2px 0 ${color}66">${w}</mark>`);

	const parseClip = (v) => {
		const parts = v.split("|").map((s) => s.trim());
		if (parts.length >= 4 && (PALETTE[parts[2]] || /^#/.test(parts[2])))
			return { tag: parts[0], date: parts[1], color: PALETTE[parts[2]] ?? parts[2], title: parts.slice(3).join(" | ") };
		if (parts.length >= 3)
			return { tag: parts[0], date: parts[1], color: "#7a6bcc", title: parts.slice(2).join(" | ") };
		if (parts.length === 2)
			return { tag: "", date: parts[0], color: "#7a6bcc", title: parts[1] };
		return { tag: "", date: "", color: "#7a6bcc", title: v };
	};

	let blocks = $derived.by(() => {
		const out = [];
		for (const raw of items ?? []) {
			const it = typeof raw === "string" ? { type: "text", value: raw } : raw;
			if (!it?.value) continue;
			if (it.type === "clip") {
				const last = out[out.length - 1];
				if (last?.kind === "clips") last.clips.push(parseClip(it.value));
				else out.push({ kind: "clips", clips: [parseClip(it.value)] });
			} else if (it.type === "chart") {
				const parts = it.value.split("|").map((x) => x.trim());
				const rawName = parts[0];
				const c = { kind: "chart", name: CHART_ALIASES[rawName] ?? rawName,
					words: [], groups: [], title: "", caption: "", from: null, to: null, steps: null };
				for (const p of parts.slice(1)) {
					if (/^title\s*:/i.test(p)) c.title = p.replace(/^title\s*:/i, "").trim();
					else if (/^caption\s*:/i.test(p)) c.caption = p.replace(/^caption\s*:/i, "").trim();
					else if (/^words\s*:/i.test(p)) c.words = p.replace(/^words\s*:/i, "").split(",").map((w) => w.trim());
						else if (/^groups\s*:/i.test(p)) c.groups = p.replace(/^groups\s*:/i, "").split("/")
							.map((g) => g.split(",").map((w) => w.trim()).filter(Boolean)).filter((g) => g.length);
					else if (/^steps\s*:/i.test(p)) {
						const key = p.replace(/^steps\s*:/i, "").trim();
						c.steps = Array.isArray(copyAll[key]) ? copyAll[key] : null;
						if (!c.steps) c.stepsMissing = key;
					}
					else if (/^years\s*:/i.test(p)) {
						const m = p.replace(/^years\s*:/i, "").trim().match(/(\d{4})\s*[-–—]?\s*(\d{4})?/);
						if (m) { c.from = m[1] + "-01"; c.to = (m[2] ?? m[1]) + "-12"; }
					}
					// month-precision window, same vocabulary as scrolly steps:
					// `from: 2020 | to: 2024-03` (bare years expand to Jan / Dec)
					else if (/^from\s*:/i.test(p)) {
						const v = p.replace(/^from\s*:/i, "").trim();
						if (v) c.from = /^\d{4}$/.test(v) ? v + "-01" : v;
					}
					else if (/^to\s*:/i.test(p)) {
						const v = p.replace(/^to\s*:/i, "").trim();
						if (v) c.to = /^\d{4}$/.test(v) ? v + "-12" : v;
					}
					// named single-value params some charts take, e.g. `nba: true`
					// or the ngram chart's `smooth: 3`
					else if (/^(who|rel|vs|pair|nba|smooth|topic|dots)\s*:/i.test(p)) {
						const [key, ...rest] = p.split(":");
						c[key.trim().toLowerCase()] = rest.join(":").trim();
					}
					else if (p) c.words = p.split(",").map((w) => w.trim());
				}
				out.push(c);
			} else if (/^embed$/i.test(it.type)) {
				// embed: <url> | caption
				// YouTube only for now, and a Short is portrait — a vertical video in a
				// 16:9 frame is mostly letterbox, so the shape has to be detected here.
				const [url, caption = ""] = it.value.split("|").map((x) => x.trim());
				const short = /\/shorts\//.test(url);
				const id = (url.match(/(?:shorts\/|watch\?v=|youtu\.be\/|embed\/)([\w-]{6,})/) ?? [])[1];
				if (id) out.push({ kind: "embed", id, short, caption });
			} else if (it.type === "img") {
				const p = it.value.split("|").map((x) => x.trim());
				out.push({ kind: "img", src: p[0], alt: p[1] ?? "", caption: p[2] ?? "" });
			} else if (it.type === "text") {
				out.push({ kind: "text", value: it.value });
			} else {
				out.push({ kind: "el", tag: it.type, value: it.value });
			}
		}
		return out;
	});
	const ROTS = [-1.8, 1.4, -1.1, 1.7, -1.5, 1.2];
</script>

{#each blocks as b}
	{#if b.kind === "text"}
		<p>{@html hl(b.value)}</p>
	{:else if b.kind === "clips"}
		<div class="receipts">
			{#each b.clips as c, i}
				<div class="clip" style="--rot: {ROTS[i % ROTS.length]}deg">
					<FoxBadge />
					{#if c.date}<span class="cdate">{c.date}</span>{/if}
					<p class="cline">{@html hl(c.title, CLIP_BLUE)}</p>
				</div>
			{/each}
		</div>
	{:else if b.kind === "chart"}
		<div class="pchart" class:hide-hed={!!b.title} class:full-bleed={FULL_BLEED.has(b.name)} class:wide={WIDE.has(b.name)}>
			{#if b.title && !SELF_CAPTIONED.has(b.name)}<h4 class="pc-title">{@html hl(b.title)}</h4>{/if}
			{#if b.name === "timeline-words"}
				<TimelineWords words={b.words} startMonth={b.from} endMonth={b.to} />
						{:else if b.name === "toc"}
				<Toc />
			{:else if b.name === "headline-table"}
				<HeadlineTable words={b.words} />
						{:else if b.name === "politicized"}
				<Politicized words={b.words} />
			{:else if b.name === "framing-tabs"}
				<FramingTabs words={b.words} />
						{:else if b.name === "player-volume"}
				<PlayerVolume words={b.words} />
						{:else if b.name === "league-rise"}
				<LeagueRise />
						{:else if b.name === "league-bars"}
				<LeagueBars />
			{:else if b.name === "player-words-scrolly"}
				<PlayerWordsScrolly steps={b.steps} />
						{:else if b.name === "outlet-gap-scrolly"}
				<OutletGapScrolly steps={b.steps} />
			{:else if b.name === "timeline-scrolly"}
				<TimelineScrolly steps={b.steps} chartName={b.words?.[0] ?? "timeline-trans"}
					title={b.title} caption={b.caption} />
			{:else if b.name === "ngram"}
				<NgramChart words={b.words} smoothing={b.smooth ?? 2} />
			{:else if b.name === "outlet-topics"}
				<OutletTopicCompare topic={b.topic ?? "polrace"} dotsTopic={b.dots ?? null} />
			{:else if b.name === "timeline-simple"}
				<TimelineSimple title={b.title} sub={b.caption} />
						{:else if b.name === "word-quadrant"}
				<WordQuadrant />
			{:else if b.name === "word-quadrant-scrolly"}
				<WordQuadrantScrolly steps={b.steps} />
			{:else if b.name === "ternary-scrolly"}
				<TernaryScrolly steps={b.steps} />
			{:else if b.name === "ternary-static"}
				<TernaryStatic words={b.words} groups={b.groups} />
						{:else if b.name === "chyron-months"}
				<ChyronRows words={b.words} from={b.from} to={b.to} />
			{:else if TIMELINE_CHARTS.has(b.name)}
				<TimelineStatic chartName={b.name} startMonth={b.from} endMonth={b.to}
					showNBA={b.nba === "true"} />
			{:else if NETWORK_SOURCES[b.name]}
				{#if b.stepsMissing}
					<p class="chart-missing">No steps array named “{b.stepsMissing}” found in the Doc</p>
				{/if}
				<NetworkScrolly steps={b.steps} source={NETWORK_SOURCES[b.name]} />
			{:else}
				<p class="chart-missing">Unknown chart: “{b.name}”</p>
			{/if}
			{#if b.caption && !SELF_CAPTIONED.has(b.name)}<p class="pc-cap">{@html b.caption}</p>{/if}
		</div>
	{:else if b.kind === "embed"}
		<figure class="pembed" class:portrait={b.short}>
			<div class="frame">
				<iframe
					src="https://www.youtube-nocookie.com/embed/{b.id}"
					title={b.caption || "Embedded video"}
					loading="lazy"
					allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
					referrerpolicy="strict-origin-when-cross-origin"
					allowfullscreen
				></iframe>
			</div>
			{#if b.caption}<figcaption>{@html b.caption}</figcaption>{/if}
		</figure>
	{:else if b.kind === "img"}
		<figure class="pimg">
			<img src="{base}/images/{b.src}" alt={b.alt} loading="lazy" />
			{#if b.caption}<figcaption>{@html b.caption}</figcaption>{/if}
		</figure>
	{:else}
		<svelte:element this={b.tag}>{@html b.value}</svelte:element>
	{/if}
{/each}

<style>
	p { font-size: 17px; line-height: 1.65; margin-bottom: 1em; color: #2a1503; }
	p :global(mark) { color: inherit; padding: 0 3px; border-radius: 2px; }
	.receipts { display: flex; flex-direction: column; gap: 12px; max-width: 560px; margin: 6px auto 26px; }
	.clip {
		background: #fffdf8;
		border: 1px solid #e6dcc3;
		box-shadow: 0 3px 12px rgba(0, 0, 0, 0.12);
		padding: 10px 15px;
		transform: rotate(var(--rot, 0deg));
	}
	.clip .cline { font-size: 15.5px; font-weight: 700; line-height: 1.4; margin: 5px 0 0; font-family: Georgia, serif; color: #1a1a1a; }
	.cdate { font-size: 12px; color: rgba(42, 21, 3, 0.55); }
	.pchart { margin: 12px 0 22px; }
	/* charts that need more than the prose column, but not the whole window */
	.pchart.wide {
		width: min(1100px, 96vw);
		margin-left: 50%;
		transform: translateX(-50%);
	}
	.pchart.full-bleed {
		width: 100vw;
		margin-left: 50%;
		transform: translateX(-50%);
		padding: 0 12px;
	}
	.pchart.hide-hed :global(.vhed), .pchart.hide-hed :global(.hed) { display: none; }
	.pc-title { font-size: 19px; text-align: center; margin: 0 0 10px; color: #2a1503; }
	.pc-cap { font-size: 12.5px; color: rgba(42, 21, 3, 0.6); margin-top: 4px; text-align: center; }
	.chart-missing { font-size: 13px; color: #a33; }
	.pembed { margin: 20px auto; max-width: 620px; }
	/* a Short is 9:16; a normal video is 16:9 — the wrong one letterboxes badly */
	.pembed.portrait { max-width: 330px; }
	.pembed .frame {
		position: relative; width: 100%; padding-top: 56.25%;
		background: rgba(42, 21, 3, 0.12); border-radius: 4px; overflow: hidden;
	}
	.pembed.portrait .frame { padding-top: 177.8%; }
	.pembed iframe {
		position: absolute; inset: 0; width: 100%; height: 100%; border: 0;
	}
	.pembed figcaption {
		font-size: 12.5px; line-height: 1.5; color: rgba(42, 21, 3, 0.62);
		text-align: center; margin-top: 7px;
	}

	.pimg {
		margin: 18px 0 26px;
		background: transparent;
		width: 100%;
		max-width: 640px;
		margin-left: auto;
		margin-right: auto;
	}
	.pimg img {
		display: block;
		width: 100%;
		border-radius: 8px;
		box-shadow: 0 4px 18px rgba(0, 0, 0, 0.18);
		border: 1px solid rgba(42, 21, 3, 0.15);
	}
	.pimg figcaption { font-size: 12.5px; color: rgba(42, 21, 3, 0.6); margin-top: 6px; text-align: center; }
</style>
