<script>
	// Fox News vs. the other outlets on one topic: Fox's line in colour, the
	// others in grey, a few dated notes, then each outlet small, then the words counted.
	//
	// In the Doc (every line but topic is optional):
	//   {.FoxVsField}
	//   topic: polrace          polrace, lgbtq or fouls
	//   second: protect         a second Fox line
	//   by: month               year (default) or month
	//   from: 2024-05           to: 2026-09
	//   title: …                kicker: …
	//   subtitle: …             {swatch}, {swatch2} and {grey} put in the colour chips
	//   notes: 2020 | Players’ BLM protests; 2024 | Caitlin Clark’s rookie season
	//   mark: 2026-07-07        markNote: …   markShort: … (phones)
	//   peakNote: … {n} …       peakNoteShort: …   ("none" hides it)
	//   lineLabel: …            line2Label: …   fieldLabel: …   unit: …
	//   listLabel: …            list2Label: …   sourceNote: …
	//   field: false            hide the grey lines
	//   {}
	import { base } from "$app/paths";
	import { scaleLinear, scalePoint } from "d3-scale";
	import { line as d3line, area as d3area } from "d3-shape";
	import rows from "$data/outlet_topics.csv";
	import monthRows from "$data/outlet_topics_monthly.csv";
	import termRows from "$data/foul_terms_monthly.csv"; // each foul word, Fox, by month
	import { COMPARISON, SHORT, LOGO } from "$utils/outlets.js";
	import { wordGroupsFor } from "$utils/topicWords.js";
	import { fill, or } from "$utils/fill.js";
	import { tidy } from "$utils/clips.js";

	// ---------------------------------------------------------------------
	// Settings for each topic
	// ---------------------------------------------------------------------
	//   color   Fox's line (fouls and protect: picked to stay apart for colour-blind readers)
	//   kicker  small label over the headline
	//   name    how the text names it (fouls by its words, not "foul words")
	//   notes   default dated notes: [period, text]
	//   fieldAt where "Other outlets" is written (fieldAtPhone on phones)
	const TOPICS = {
		polrace: {
			color: "#B91C1C",
			kicker: "Race",
			name: "race",
			notes: [
				["2020", "Players’ BLM protests"],
				["2024", "Caitlin Clark’s rookie season"]
			],
			fieldAt: "2021",
			fieldAtPhone: "2022"
		},
		lgbtq: {
			color: "#B91C1C",
			kicker: "LGBTQ+",
			name: "LGBTQ+ topics",
			notes: [],
			fieldAt: "2022"
		},
		fouls: {
			color: "#B91C1C",
			kicker: "Fouls",
			name: "hip-check, poke, punch or throat",
			notes: [],
			fieldAt: "2025-01"
		},
		protect: {
			color: "#7C7060",
			kicker: "Protect",
			name: "“protect”",
			notes: []
		}
	};
	// fouls only: Fox's busiest month gets this note
	const PEAK_NOTE = {
		fouls: ["Clark’s rookie summer: {n} Fox articles", "Clark’s rookie summer"]
	};
	const MARK_NOTE = ["Republicans’ letter to the WNBA", "Republicans’ letter"]; // default for `mark`
	const MIN_N = 20; // years with fewer articles than this aren't drawn

	let {
		topic = "polrace",
		second = null,
		by = "year",
		from = "",
		to = "",
		title = "",
		kicker = "",
		subtitle = "",
		notes = null,
		mark = "",
		markNote = "",
		markLabel = "", // older name for markNote
		markShort = "",
		lineLabel = "",
		line2Label = "",
		fieldLabel: fieldName = "",
		unit = "",
		peakNote = "",
		peakNoteShort = "",
		listLabel = "",
		list2Label = "",
		sourceNote = "",
		field: showField = null,
		...rest // old options still in the Doc
	} = $props();

	const FOX = "Fox News";
	const T = TOPICS[topic];
	const COLOR = Object.fromEntries(
		Object.entries(TOPICS).map(([k, v]) => [k, v.color])
	);
	const NAME = Object.fromEntries(
		Object.entries(TOPICS).map(([k, v]) => [k, v.name])
	);
	const monthly = String(by).trim().toLowerCase() === "month";
	// by year: share of articles; by month: counts (a month's share is too noisy)
	const counts = monthly;

	// ---------------------------------------------------------------------
	// Data: table[topic][outlet][period] = { n, hit }
	// ---------------------------------------------------------------------

	const table = {};
	for (const r of monthly ? monthRows : rows) {
		if (r.method !== "body") continue;
		((table[r.topic] ??= {})[r.outlet] ??= {})[monthly ? r.period : r.year] = {
			n: +r.articles,
			hit: +r.hits
		};
	}
	const key = (v) =>
		!v
			? ""
			: monthly
				? String(v).trim().slice(0, 7)
				: String(v).trim().slice(0, 4);
	const FROM = key(from),
		TO = key(to);
	const periods = [
		...new Set(Object.values(table[topic] ?? {}).flatMap((o) => Object.keys(o)))
	]
		.filter((p) => (!FROM || p >= FROM) && (!TO || p <= TO))
		.sort();
	const others = COMPARISON.filter((o) => table[topic]?.[o]);
	const outlets = [FOX, ...others];

	const valueOf = (t, o, p) => {
		const c = table[t]?.[o]?.[p];
		if (!c) return counts ? 0 : null;
		if (counts) return c.hit;
		return c.n >= MIN_N ? c.hit / c.n : null;
	};
	const series = (t, o) =>
		periods.map((p) => ({ p, v: valueOf(t, o, p) })).filter((d) => d.v != null);
	// one number for the whole span (the small panels' totals)
	const overall = (t, o) => {
		const cells = periods.map((p) => table[t]?.[o]?.[p]).filter(Boolean);
		const hit = cells.reduce((s, c) => s + c.hit, 0),
			n = cells.reduce((s, c) => s + c.n, 0);
		return counts ? hit : n ? hit / n : 0;
	};

	// ---------------------------------------------------------------------
	// Lines
	// ---------------------------------------------------------------------

	// long names go on two lines, split at the comma nearest the middle
	const nameLines = (name) => {
		if (name.length <= 20) return [name];
		const cuts = [...name.matchAll(/, /g)].map((m) => m.index);
		if (!cuts.length) return [name];
		const at = cuts.reduce((a, b) =>
			Math.abs(b - name.length / 2) < Math.abs(a - name.length / 2) ? b : a
		);
		return [name.slice(0, at + 1), name.slice(at + 2)];
	};
	const cap = (t) => t.replace(/^(“?)(\w)/, (_, q, c) => q + c.toUpperCase());
	// Fox's line(s): with two, each is named by its words
	const heroes = [topic, ...(second ? [second] : [])].map((t) => ({
		t,
		color: COLOR[t],
		name: or(
			t === topic ? lineLabel : line2Label,
			second ? cap(NAME[t]) : "Fox News"
		),
		pts: series(t, FOX)
	}));
	// the grey lines; off by default when Fox has two lines (the small panels compare instead)
	const withField =
		showField == null ? !second : String(showField).toLowerCase() !== "false";
	const field = withField
		? others.map((o) => ({ o, pts: series(topic, o) }))
		: [];

	const peak = Math.max(
		...heroes.flatMap((h) => h.pts.map((d) => d.v)),
		...field.flatMap((f) => f.pts.map((d) => d.v)),
		0
	);
	const step = counts ? (peak > 60 ? 20 : 10) : 0.1;
	const yMax = Math.ceil((peak * 1.04) / step) * step;
	const yTicks = Array.from(
		{ length: Math.round(yMax / step) + 1 },
		(_, i) => +(i * step).toFixed(4)
	);
	const fmt = (v) =>
		counts ? String(Math.round(v)) : `${Math.round(v * 100)}%`;
	const MONTHS = [
		"Jan.",
		"Feb.",
		"March",
		"April",
		"May",
		"June",
		"July",
		"Aug.",
		"Sept.",
		"Oct.",
		"Nov.",
		"Dec."
	];
	const edge = (p) =>
		monthly
			? `${MONTHS[+p.slice(5, 7) - 1].replace(".", "")} ’${p.slice(2, 4)}`
			: p;
	const periodName = (p) =>
		monthly ? `${MONTHS[+p.slice(5, 7) - 1]} ${p.slice(0, 4)}` : p;

	// ---------------------------------------------------------------------
	// Dated notes: the Doc's, or the topic's; fouls' peak; the `mark` date
	// ---------------------------------------------------------------------

	const markKey = key(mark);
	const peakOf = (pts) =>
		pts.reduce((a, b) => (b.v > a.v ? b : a), pts[0] ?? { v: 0 });
	const noteList = (() => {
		const given =
			notes != null && String(notes).trim()
				? String(notes)
						.split(";")
						.map((s) => s.split("|").map((x) => x.trim()))
						.filter((n) => n[0] && n[1])
				: T.notes;
		const out = given.map(([p, text]) => ({ p: key(p), head: p, text }));
		const [peakDefault, peakShortDefault] =
			notes == null ? (PEAK_NOTE[topic] ?? ["", ""]) : ["", ""];
		const peakText = or(peakNote, peakDefault);
		if (peakText && peakText.toLowerCase() !== "none" && heroes[0].pts.length) {
			const top = peakOf(heroes[0].pts);
			const short = or(
				peakNoteShort,
				String(peakNote).trim() ? "" : peakShortDefault
			);
			out.push({
				p: top.p,
				head: periodName(top.p),
				text: fill(peakText, { n: fmt(top.v) }),
				short: fill(short, { n: fmt(top.v) })
			});
		}
		const markText = or(markNote, or(markLabel, ""));
		if (markKey && periods.includes(markKey))
			out.push({
				p: markKey,
				head: new Date(mark + "T12:00").toLocaleDateString("en-US", {
					month: "long",
					day: "numeric",
					year: "numeric"
				}),
				text: markText || MARK_NOTE[0],
				short: or(markShort, markText ? "" : MARK_NOTE[1]),
				left: true
			});
		return out.filter((n) => periods.includes(n.p));
	})();
	// a note on up to three short lines
	const wrap = (text, width = 22) => {
		const lines = [""];
		for (const w of text.split(/\s+/)) {
			const cur = lines[lines.length - 1];
			if ((cur + " " + w).trim().length > width && cur) lines.push(w);
			else lines[lines.length - 1] = (cur + " " + w).trim();
		}
		return lines;
	};

	// fouls: each word written on the line at its busiest month
	const wordPeaks = (() => {
		if (topic !== "fouls") return [];
		const best = {};
		for (const r of termRows) {
			if (r.outlet !== FOX || !periods.includes(r.period)) continue;
			const k = +r.hits;
			if (!best[r.term] || k > best[r.term].k)
				best[r.term] = { p: r.period, k };
		}
		const byMonth = {};
		for (const [term, b] of Object.entries(best))
			(byMonth[b.p] ??= []).push({ term, k: b.k });
		return Object.entries(byMonth).map(([p, words]) => ({
			p,
			v: valueOf(topic, FOX, p),
			words: words.sort((a, b) => b.k - a.k)
		}));
	})();

	// ---------------------------------------------------------------------
	// Layout
	// ---------------------------------------------------------------------

	let width = $state(640);
	const narrow = $derived(width < 520);
	// the chart's height: at least this, and taller when its box is stretched
	// (beside a taller triangle in a SideBySide, it fills the column)
	const MIN_H = $derived(narrow ? 300 : 340);
	let boxH = $state(0);
	const H = $derived(Math.max(MIN_H, Math.round(boxH)));
	const M = $derived({
		top: 28,
		right: narrow ? 72 : 100,
		bottom: 30,
		left: 4
	});
	const x = $derived(
		scalePoint()
			.domain(periods)
			.range([M.left + 30, width - M.right])
	);
	const y = $derived(
		scaleLinear()
			.domain([0, yMax])
			.range([H - M.bottom, M.top])
	);
	const path = $derived(
		d3line()
			.x((d) => x(d.p))
			.y((d) => y(d.v))
	);
	const xLabel = (p, i) => {
		if (!monthly) return !narrow ? p : +p % 2 ? "" : "’" + p.slice(2); // phones: even years only
		if (i === 0) return `${MONTHS[+p.slice(5, 7) - 1]} ${p.slice(0, 4)}`;
		if (p.endsWith("-01")) return p.slice(0, 4);
		return !narrow && p.endsWith("-07") && i > 3
			? `July ’${p.slice(2, 4)}`
			: "";
	};

	// Labels on Fox's lines: one line is named at its end; two lines at
	// their highest points, kept clear of the notes and of each other
	const heroLabels = $derived.by(() => {
		const placed = [];
		return heroes.map((h, k) => {
			if (k === 0 && wordPeaks.length) return null;
			const place = (d, value, dy) => {
				const w =
					Math.max(...nameLines(h.name).map((l) => l.length), value.length) *
					7.2;
				const right = x(d.p) + 8 + w <= width; // flip left if it would run off the edge
				return {
					x: right ? x(d.p) + 8 : x(d.p) - 8,
					y: y(d.v) + dy,
					value,
					anchor: right ? "start" : "end"
				};
			};
			if (!second) {
				const last = h.pts[h.pts.length - 1];
				return last && place(last, fmt(last.v), 4);
			}
			const rightNotes = noteList
				.filter((n) => k === 0 || !n.left)
				.map((n) => periods.indexOf(n.p));
			const clear = (d) => {
				const lx = x(d.p) + 8,
					ly = y(d.v) - 4;
				return (
					rightNotes.every((i) => Math.abs(periods.indexOf(d.p) - i) > 2) &&
					placed.every(
						(q) => Math.abs(q.x - lx) > 120 || Math.abs(q.y - ly) > 34
					)
				);
			};
			const best =
				[...h.pts].sort((a, b) => b.v - a.v).find(clear) ?? peakOf(h.pts);
			const extra = (nameLines(h.name).length - 1) * 15;
			const at = place(
				best,
				narrow
					? `${fmt(best.v)}, ${edge(best.p)}`
					: `${fmt(best.v)} in ${periodName(best.p)}`,
				-4 - extra
			);
			placed.push(at);
			return at;
		});
	});

	// "Other outlets", written once above the grey lines at the topic's fieldAt
	const fieldLabel = $derived.by(() => {
		const want = (narrow && T.fieldAtPhone) || T.fieldAt;
		const p = periods.includes(want)
			? want
			: periods[Math.floor(periods.length / 3)];
		const near = periods.filter(
			(q) => Math.abs(x(q) - x(p)) < (narrow ? 40 : 75)
		);
		const top = Math.max(
			...near.flatMap((q) =>
				[...field, ...heroes].map((s) => s.pts.find((d) => d.p === q)?.v ?? 0)
			)
		);
		const notesFoot = noteList.length ? M.top + 16 + 14 * 3 + 16 : 0; // stay below the notes
		return { p, v: top, y: Math.max(y(top) - 8, notesFoot) };
	});

	// ---------------------------------------------------------------------
	// Hover
	// ---------------------------------------------------------------------

	let hover = $state(null);
	function onMove(e) {
		const box = e.currentTarget.getBoundingClientRect();
		const px = e.clientX - box.left;
		let i = 0,
			d = Infinity;
		periods.forEach((p, k) => {
			const dist = Math.abs(x(p) - px);
			if (dist < d) ((d = dist), (i = k));
		});
		const p = periods[i];
		const rows = [
			...heroes.map((h) => ({
				name: second ? h.name : FOX,
				o: FOX,
				v: valueOf(h.t, FOX, p),
				hi: true
			})),
			...(withField ? others : []).map((o) => ({
				name: SHORT[o] ?? o,
				o,
				v: valueOf(topic, o, p)
			}))
		].filter((r) => r.v != null);
		rows.sort((a, b) => b.v - a.v);
		hover = { p, px: x(p), rows };
	}

	// ---------------------------------------------------------------------
	// Small panels, text
	// ---------------------------------------------------------------------

	const SW = 200,
		SH = 70,
		SM = { t: 4, r: 4, b: 14, l: 4 };
	const sx = scalePoint()
		.domain(periods)
		.range([SM.l, SW - SM.r]);
	const sy = scaleLinear()
		.domain([0, yMax])
		.range([SH - SM.b, SM.t]);
	const spath = d3line()
		.x((d) => sx(d.p))
		.y((d) => sy(d.v));
	const sarea = d3area()
		.x((d) => sx(d.p))
		.y0(sy(0))
		.y1((d) => sy(d.v));

	const what = monthly
		? "articles each month"
		: "share of each outlet’s WNBA articles";
	const words = wordGroupsFor(topic, second).map((g, i) => ({
		...g,
		label: or(i ? list2Label : listLabel, g.label)
	}));
	const swatch = (c) => `<span class="sw" style="background:${c}"></span>`;
	const dekDefault = second
		? `Fox News WNBA articles each month that use {swatch}<b>${NAME[topic]}</b>${NAME[topic].includes(" or ") ? ", or" : " or"} {swatch2}<b>${NAME[second]}</b>.` +
			(withField
				? ` In grey, each other outlet’s articles with ${NAME[topic]}.`
				: "")
		: `Share of each outlet’s WNBA articles that mention ${NAME[topic]}, by ${monthly ? "month" : "year"}.<br />{swatch}<b>Fox News</b> and {grey}${others.length === 6 ? "six" : others.length} other outlets.`;
	const dek = tidy(fill(or(subtitle, dekDefault), {
		swatch: swatch(COLOR[topic]),
		swatch2: second ? swatch(COLOR[second]) : "",
		grey: '<span class="sw grey"></span>'
	}));
</script>

<figure class="fvf" bind:clientWidth={width}>
	<!-- <p class="kicker" style:color={COLOR[topic]}>{kicker || T.kicker || ""}</p> -->
	<p class="kicker">on the web</p>
	<p class="dek">
		{@html dek}
	</p>

	<div class="main" style:min-height="{MIN_H}px" bind:clientHeight={boxH}>
		<svg
			{width}
			height={H}
			role="img"
			aria-label="{title ||
				what}, Fox News against {others.length} other outlets"
		>
			<!-- gridlines; the top one says the unit -->
			{#each yTicks as t, i (t)}
				{#if t > 0}
					<line
						class="grid"
						x1={M.left}
						x2={width - M.right + 10}
						y1={y(t)}
						y2={y(t)}
					/>
					<text class="gtext" x={M.left} y={y(t) - 5}
						>{fmt(t)}{i === yTicks.length - 1
							? " " + or(unit, counts ? "articles" : "of articles")
							: ""}</text
					>
				{/if}
			{/each}
			<line
				class="base"
				x1={M.left}
				x2={width - M.right + 10}
				y1={y(0)}
				y2={y(0)}
			/>
			{#each periods as p, i (p)}
				{@const lab = xLabel(p, i)}
				{#if lab}<text class="xtext" x={x(p)} y={H - 8} text-anchor="middle"
						>{lab}</text
					>{/if}
			{/each}

			<!-- the dated notes -->
			{#each noteList as n (n.p + n.text)}
				{@const nx = x(n.p)}
				{@const tx = nx + (n.left ? -6 : 6)}
				<line class="note-line" x1={nx} x2={nx} y1={M.top - 4} y2={y(0)} />
				<text
					class="note"
					x={tx}
					y={M.top + 16}
					text-anchor={n.left ? "end" : "start"}
				>
					<tspan class="note-head" x={tx}>{n.head}</tspan>
					{#each wrap(narrow && n.short ? n.short : n.text, narrow ? 13 : 22) as l, k (k)}<tspan
							x={tx}
							dy="14">{l}</tspan
						>{/each}
				</text>
			{/each}

			<!-- the other outlets, grey -->
			{#each field as f (f.o)}
				<path class="field" d={path(f.pts)} />
			{/each}
			<!-- no line labels on phones for two-line charts; the subtitle names them -->
			{#if withField && fieldLabel && !(narrow && second)}
				<text
					class="field-label"
					x={x(fieldLabel.p)}
					y={fieldLabel.y - 10}
					text-anchor="middle"
					>{or(
						fieldName,
						`Other outlets${second ? `’ ${NAME[topic]}` : ""}`
					)}</text
				>
			{/if}

			<!-- Fox -->
			{#each heroes as h, k (h.t)}
				<path class="hero" d={path(h.pts)} stroke={h.color} />
				{#if !monthly}
					{#each h.pts as d (d.p)}
						<circle
							class="hero-dot"
							cx={x(d.p)}
							cy={y(d.v)}
							r="4"
							fill={h.color}
						/>
					{/each}
				{/if}
				{#if heroLabels[k] && !(narrow && second)}
					<text
						class="hero-label"
						x={heroLabels[k].x}
						y={heroLabels[k].y}
						fill={h.color}
						text-anchor={heroLabels[k].anchor}
					>
						{#each nameLines(h.name) as l, j (j)}<tspan
								x={heroLabels[k].x}
								dy={j ? 15 : 0}>{l}</tspan
							>{/each}
						<tspan class="hero-value" x={heroLabels[k].x} dy="15"
							>{heroLabels[k].value}</tspan
						>
					</text>
				{/if}
			{/each}

			<!-- fouls: each word at its busiest month -->
			{#each wordPeaks as w (w.p)}
				{@const px = x(w.p)}
				{@const left = px > width * 0.72}
				{@const lx = px + (left ? -9 : 9)}
				<text
					class="word-label"
					x={lx}
					y={y(w.v) - (w.words.length - 1) * 7.5 + 4}
					fill={COLOR[topic]}
					text-anchor={left ? "end" : "start"}
				>
					{#each w.words as t, j (t.term)}<tspan x={lx} dy={j ? 15 : 0}
							><tspan class="word-term">{t.term}</tspan> {t.k}</tspan
						>{/each}
				</text>
			{/each}

			{#if hover}
				<line
					class="cross"
					x1={hover.px}
					x2={hover.px}
					y1={M.top - 4}
					y2={y(0)}
				/>
			{/if}
			<rect
				x={M.left}
				y="0"
				width={Math.max(0, width - M.left - M.right + 10)}
				height={H}
				fill="transparent"
				role="presentation"
				onpointermove={onMove}
				onpointerleave={() => (hover = null)}
			/>
		</svg>
		{#if hover}
			<div
				class="tip"
				class:plain={topic === "fouls"}
				style:left="{Math.min(
					width - 190,
					Math.max(0, hover.px + (hover.px > width / 2 ? -210 : 10))
				)}px"
				style:top="{M.top}px"
			>
				<p class="tip-t">{periodName(hover.p)}</p>
				{#each hover.rows as r (r.name)}
					<p class="tip-row" class:hi={r.hi}>
						<span class="tip-name">
							{#if LOGO[r.o] && topic !== "fouls"}<img class="logo" alt="" src="{base}/logos/square/{LOGO[r.o]}" />{/if}
							{r.name}
						</span><span>{fmt(r.v)}</span>
					</p>
				{/each}
			</div>
		{/if}
	</div>

	<!-- each outlet on its own, same scale -->
	

	<!-- the words counted -->
	<div class="source">
		{#each words as g (g.label)}
			<p><b>{g.label}:</b> {g.words.join(", ")}</p>
		{/each}
		<p>
			{@html tidy(
				or(sourceNote, "An article counts once, however often it uses them.")
			)}
		</p>
	</div>
</figure>

<style>
	.fvf {
		width: 100%;
		margin: 0;
		font-family: var(--font-graphic);
		color: var(--color-ink-dark);
	}
	.hed {
		margin: 0 0 8px;
		font-family: var(--font-graphic);
		font-size: 24px;
		font-weight: 700;
		line-height: 1.22;
		letter-spacing: -0.01em;
	}
	.dek {
		margin: 0 0 18px;
		font-size: 18px;
		line-height: 1.15;
		color: var(--color-gray-950);
		font-weight: 700;
	}
	.dek :global(b) {
		font-weight: 700;
		color: var(--color-ink-dark);
	}
	.dek :global(.sw) {
		display: inline-block;
		width: 14px;
		height: 3px;
		border-radius: 2px;
		margin-right: 3px;
		vertical-align: 4px;
	}
	.dek :global(.sw.grey) {
		background: #7C7060;
	}
	/* the chart box takes whatever room the column leaves; the svg sits on top of it
	   (out of the flow) so its own height never props the box open */
	.fvf {
		display: flex;
		flex-direction: column;
		flex: 1 1 auto;
	}
	/* the flex column would stretch it across; it stays as wide as its words */
	.fvf .kicker {
		align-self: flex-start;
	}
	.main {
		position: relative;
		flex: 1 1 auto;
	}
	.main > svg {
		position: absolute;
		top: 0;
		left: 0;
	}
	svg text {
		font-family: var(--font-graphic);
	}
	.grid {
		stroke: #e2e2e2;
	}
	.gtext,
	.xtext {
		fill: #727272;
		font-size: 12px;
	}
	.base {
		stroke: var(--color-fg);
		stroke-width: 1;
	}
	.field {
		fill: none;
		stroke: var(--wnba-tan-dark);
		opacity: 0.33;
		stroke-width: 1.25px;
	}
	.field-label {
		fill: var(--wnba-tan-dark);
		font-size: 13px;
		font-weight: 600;
	}
	.hero {
		fill: none;
		stroke-width: 3px;
		stroke-linejoin: round;
		stroke-linecap: round;
	}
	.hero-dot {
		stroke: #fff;
		stroke-width: 1.5px;
	}
	.hero-label {
		font-size: 13px;
		font-weight: 700;
	}
	.word-label {
		font-size: 13px;
	}
	.word-term {
		font-weight: 700;
	}
	.hero-value {
		fill: var(--color-ink-dark);
	}
	.note-line {
		stroke: #4a4a4a;
		stroke-width: 1;
		stroke-dasharray: 2 3;
	}
	.note {
		font-size: 12px;
		fill: #4a4a4a;
	}
	.note-head {
		font-weight: 700;
		fill: var(--color-fg);
	}
	.cross {
		stroke: var(--color-fg);
		stroke-width: 2;
	}
	.tip {
		position: absolute;
		z-index: 4;
		width: 200px;
		padding: 0.75rem 1rem;
		background: var(--color-white);
		border: 1px solid var(--color-rule);
		border-radius: 4px;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.12);
		font-size: 12.5px;
		pointer-events: none;
	}
	.tip p {
		margin: 0;
	}
	.tip-t {
		font-weight: 700;
		font-family: var(--font-serif);
		font-size: 18px;
		margin-bottom: 1rem !important;
	}
	.tip-row {
		display: flex;
		justify-content: space-between;
		gap: 24px;
		line-height: 1.5;
		color: var(--color-fg);
		border-bottom: 1px solid var(--wnba-tan-light);
		padding: 0.125rem 0;
	}
	.tip-row:last-child {
		border-bottom: none;
	}
	.tip-row.hi {
		color: var(--wnba-red);
		font-weight: 700;
		line-height: 1.2;
		padding: 0.125rem 0;
	}
	/* the fouls chart: Fox's lines only, so no logos and no red */
	.tip.plain .tip-row.hi {
		color: var(--color-fg);
		font-weight: 400;
	}
	/* with no logos to hold the rows open, the padding does it */
	.tip.plain .tip-row {
		line-height: 1.5;
		padding: 0.375rem 0;
	}
	.tip-name {
		display: flex;
		align-items: center;
		gap: 6px;
	}
	.tip-name .logo {
		display: block;
		width: 24px;
		height: 24px;
	}
	.tip-row span:last-child {
		font-variant-numeric: tabular-nums;
	}
	.strip {
		width: calc(100% - 5rem);
		margin-top: 30px;
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 16px 18px;
	}
	.sm-name {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 6px;
		margin: 0 0 2px;
		font-size: 13px;
		font-weight: 700;
	}
	.sm-name .logo {
			height: 24px;
			width: 24px;
			margin-right: 0.25rem;
		}
	.sm-name span {
		display: flex;
		align-items: center;
	}
	.sm-name span:last-child {
		font-size: 12px;
		font-weight: 600;
		color: #4a4a4a;
		font-variant-numeric: tabular-nums;
		white-space: nowrap;
	}
	.sm svg {
		display: block;
		width: 100%;
		height: auto;
		overflow: visible;
	}
	.sm-line {
		fill: none;
		stroke-width: 1.75px;
		stroke-linejoin: round;
		vector-effect: non-scaling-stroke;
	}
	.sm-area {
		opacity: 0.12;
	}
	.sm-base {
		stroke: #727272;
		stroke-width: 1;
		vector-effect: non-scaling-stroke;
	}
	.sm-tick {
		fill: #727272;
		font-size: 10px;
	}
	.source {
		margin: 22px 0 0;
		padding-top: 10px;
		border-top: 1px solid #e2e2e2;
		font-size: 12px;
		line-height: 1.5;
		color: #727272;
	}
	.source p {
		margin: 0 0 2px;
	}
	.source :global(b) {
		font-weight: 600;
		color: #4a4a4a;
	}
	@media (max-width: 560px) {
		.hed {
			font-size: 21px;
		}
		.strip {
			grid-template-columns: repeat(2, minmax(0, 1fr));
		}
	}
</style>
