<script>
	// Fox News against the field, after the Times's way with such charts
	// (2026-10-02): one chart that makes the comparison, Fox in its topic's
	// colour over every other outlet in grey, the lines labelled where they
	// are and a few dated notes; then each outlet on its own, small, on one
	// scale; then the words counted.
	//
	//   {.FoxVsField}
	//   topic: polrace        (polrace, lgbtq or fouls)
	//   second: protect       (optional: a second Fox line, as fouls has)
	//   by: month             (year, the default, or month)
	//   from: 2024-05         to: 2026-09   (optional span)
	//   title: The finding, as a headline
	//   subtitle: …           (optional: replaces the line saying what is counted)
	//   notes: 2020 | Players’ BLM protests; 2024 | Caitlin Clark’s rookie season
	//                         (optional: replaces the topic's default notes)
	//   mark: 2026-07-07      markNote: Republicans’ letter to the WNBA
	//   markShort: …          (the note on a phone)
	//   lineLabel: …  line2Label: …   (the names on Fox's lines)
	//   fieldLabel: Other outlets     (the grey lines' name)
	//   unit: of articles             (after the top gridline's number)
	//   peakNote: Clark’s rookie summer: {n} Fox articles   (fouls; "none" hides it)
	//   peakNoteShort: …
	//   listLabel: …  list2Label: …   (the word lists' names under the chart)
	//   sourceNote: An article counts once, however often it uses them.
	//   {}
	// the subtitle can place the key's colours: {swatch} (Fox's line),
	// {swatch2} (the second line), {grey} (the other outlets)
	import { scaleLinear, scalePoint } from "d3-scale";
	import { line as d3line, area as d3area } from "d3-shape";
	import rows from "$data/outlet_topics.csv";
	import monthRows from "$data/outlet_topics_monthly.csv";
	// each foul word's Fox articles by month (notebooks/outlet_topics_monthly.py)
	import termRows from "$data/foul_terms_monthly.csv";
	import { COMPARISON, SHORT } from "$utils/outlets.js";
	import { wordGroupsFor } from "$utils/topicWords.js";
	import { fill, or } from "$utils/fill.js";

	let {
		topic = "polrace",
		second = null,
		by = "year",
		from = "",
		to = "",
		title = "",
		// the small coloured label over the headline; the topic's name unless
		// the Doc gives one
		kicker = "",
		subtitle = "",
		notes = null,
		mark = "",
		markNote = "",
		// the older blocks' name for markNote
		markLabel = "",
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
		// the other outlets in grey behind Fox; left out where Fox has two
		// lines (fouls), which the small panels below compare instead
		field: showField = null,
		// accepted from the Doc's older chart blocks and not used here
		...rest
	} = $props();

	const FOX = "Fox News";
	const monthly = String(by).trim().toLowerCase() === "month";
	const MIN_N = 20; // a year with fewer articles than this is not drawn
	// shares for the yearly topics; for the months, articles (a month's share
	// of a small outlet's handful is noise)
	const counts = monthly;

	// --- the data: {outlet: {period: {n, hit}}} for each topic -----------------
	const table = {};
	for (const r of monthly ? monthRows : rows) {
		if (r.method !== "body") continue;
		((table[r.topic] ??= {})[r.outlet] ??= {})[monthly ? r.period : r.year] = { n: +r.articles, hit: +r.hits };
	}
	const key = (v) => (!v ? "" : monthly ? String(v).trim().slice(0, 7) : String(v).trim().slice(0, 4));
	const FROM = key(from), TO = key(to);
	const periods = [...new Set(Object.values(table[topic] ?? {}).flatMap((o) => Object.keys(o)))]
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
	const series = (t, o) => periods.map((p) => ({ p, v: valueOf(t, o, p) })).filter((d) => d.v != null);
	// the whole span at once: an outlet's pooled share, or its total articles
	const overall = (t, o) => {
		const cells = periods.map((p) => table[t]?.[o]?.[p]).filter(Boolean);
		const hit = cells.reduce((s, c) => s + c.hit, 0), n = cells.reduce((s, c) => s + c.n, 0);
		return counts ? hit : n ? hit / n : 0;
	};

	// --- colours: the topic's for Fox, grey for the field ----------------------
	const COLOR = {
		polrace: "var(--color-politics)",
		lgbtq: "var(--color-lgbtq)",
		// the brown and navy of the word chart, set so the two stay apart for
		// colour-blind readers (checked with the dataviz palette validator)
		fouls: "#9a5b13",
		protect: "#2f5d9e"
	};
	const KICKER = { polrace: "Race", lgbtq: "LGBTQ+", fouls: "Fouls" };
	// the fouls topic by its words, never "foul words": the four the
	// Republicans' letter cited are the point
	const NAME = { polrace: "race", lgbtq: "LGBTQ+ topics", fouls: "hip-check, poke, punch or throat", protect: "“protect”" };
	// a long line name over two lines, broken at the comma nearest its middle
	const nameLines = (name) => {
		if (name.length <= 20) return [name];
		const cuts = [...name.matchAll(/, /g)].map((m) => m.index);
		if (!cuts.length) return [name];
		const at = cuts.reduce((a, b) => (Math.abs(b - name.length / 2) < Math.abs(a - name.length / 2) ? b : a));
		return [name.slice(0, at + 1), name.slice(at + 2)];
	};
	const cap = (t) => t.replace(/^(“?)(\w)/, (_, q, c) => q + c.toUpperCase());
	const heroes = [topic, ...(second ? [second] : [])].map((t) => ({
		t,
		color: COLOR[t],
		// with only Fox drawn, each line is named by its words alone
		name: or(t === topic ? lineLabel : line2Label, second ? cap(NAME[t]) : "Fox News"),
		pts: series(t, FOX)
	}));
	const withField = showField == null ? !second : String(showField).toLowerCase() !== "false";
	const field = withField ? others.map((o) => ({ o, pts: series(topic, o) })) : [];

	// --- the scale ------------------------------------------------------------
	const peak = Math.max(...heroes.flatMap((h) => h.pts.map((d) => d.v)), ...field.flatMap((f) => f.pts.map((d) => d.v)), 0);
	const step = counts ? (peak > 60 ? 20 : 10) : peak > 0.3 ? 0.1 : 0.1;
	const yMax = Math.ceil((peak * 1.04) / step) * step;
	const yTicks = Array.from({ length: Math.round(yMax / step) + 1 }, (_, i) => +(i * step).toFixed(4));
	const fmt = (v) => (counts ? String(Math.round(v)) : `${Math.round(v * 100)}%`);
	const MONTHS = ["Jan.", "Feb.", "March", "April", "May", "June", "July", "Aug.", "Sept.", "Oct.", "Nov.", "Dec."];
	const edge = (p) => (monthly ? `${MONTHS[+p.slice(5, 7) - 1].replace(".", "")} ’${p.slice(2, 4)}` : p);
	const periodName = (p) => (monthly ? `${MONTHS[+p.slice(5, 7) - 1]} ${p.slice(0, 4)}` : p);

	// --- the dated notes --------------------------------------------------------
	// "2020 | Players’ BLM protests; 2024 | …": a period, then the note
	const DEFAULT_NOTES = {
		polrace: [["2020", "Players’ BLM protests"], ["2024", "Caitlin Clark’s rookie season"]],
		lgbtq: [],
		fouls: []
	};
	const markKey = key(mark);
	const peakOf = (pts) => pts.reduce((a, b) => (b.v > a.v ? b : a), pts[0] ?? { v: 0 });
	const noteList = (() => {
		const given = notes != null && String(notes).trim()
			? String(notes).split(";").map((s) => s.split("|").map((x) => x.trim())).filter((n) => n[0] && n[1])
			: DEFAULT_NOTES[topic] ?? [];
		const out = given.map(([p, text]) => ({ p: key(p), head: p, text }));
		// fouls: Fox's highest month, named; the dated letter, from `mark`
		const peakText = or(peakNote, topic === "fouls" && notes == null ? "Clark’s rookie summer: {n} Fox articles" : "");
		if (peakText && peakText.toLowerCase() !== "none" && heroes[0].pts.length) {
			const top = peakOf(heroes[0].pts);
			const short = or(peakNoteShort, topic === "fouls" && !String(peakNote).trim() ? "Clark’s rookie summer" : "");
			out.push({ p: top.p, head: periodName(top.p), text: fill(peakText, { n: fmt(top.v) }), short: fill(short, { n: fmt(top.v) }) });
		}
		const markText = or(markNote, or(markLabel, ""));
		if (markKey && periods.includes(markKey))
			out.push({
				p: markKey,
				head: new Date(mark + "T12:00").toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" }),
				text: markText || "Republicans’ letter to the WNBA",
				short: or(markShort, markText ? "" : "Republicans’ letter"),
				left: true
			});
		return out.filter((n) => periods.includes(n.p));
	})();
	// a note's words on up to three short lines
	const wrap = (text, width = 22) => {
		const lines = [""];
		for (const w of text.split(/\s+/)) {
			const cur = lines[lines.length - 1];
			if ((cur + " " + w).trim().length > width && cur) lines.push(w);
			else lines[lines.length - 1] = (cur + " " + w).trim();
		}
		return lines;
	};

	// --- the fouls words, each named on the line at its busiest month ----------
	// ("hip-check" on the June 2024 spike, "poke" on June 2025's, …), words
	// that peak in the same month listed together, busiest first
	const wordPeaks = (() => {
		if (topic !== "fouls") return [];
		const best = {};
		for (const r of termRows) {
			if (r.outlet !== FOX || !periods.includes(r.period)) continue;
			const k = +r.hits;
			if (!best[r.term] || k > best[r.term].k) best[r.term] = { p: r.period, k };
		}
		const byMonth = {};
		for (const [term, b] of Object.entries(best)) (byMonth[b.p] ??= []).push({ term, k: b.k });
		return Object.entries(byMonth).map(([p, words]) => ({
			p,
			v: valueOf(topic, FOX, p),
			words: words.sort((a, b) => b.k - a.k)
		}));
	})();

	// --- layout -----------------------------------------------------------------
	let width = $state(640);
	const narrow = $derived(width < 520);
	const H = $derived(narrow ? 300 : 340);
	const M = $derived({ top: 28, right: narrow ? 72 : 100, bottom: 30, left: 4 });
	const x = $derived(scalePoint().domain(periods).range([M.left + 30, width - M.right]));
	const y = $derived(scaleLinear().domain([0, yMax]).range([H - M.bottom, M.top]));
	const path = $derived(d3line().x((d) => x(d.p)).y((d) => y(d.v)));
	const xLabel = (p, i) => {
		// on a phone, the even years alone, shortened
		if (!monthly) return !narrow ? p : +p % 2 ? "" : "’" + p.slice(2);
		if (i === 0) return `${MONTHS[+p.slice(5, 7) - 1]} ${p.slice(0, 4)}`;
		if (p.endsWith("-01")) return p.slice(0, 4);
		return !narrow && p.endsWith("-07") && i > 3 ? `July ’${p.slice(2, 4)}` : "";
	};
	// where each Fox line is named: a single line at its end; two lines at
	// their highest points, clear of the notes whose words run the same way
	// (rightward) and of each other
	const heroLabels = $derived.by(() => {
		const placed = [];
		return heroes.map((h, k) => {
			if (k === 0 && wordPeaks.length) return null;
			// a label that would run past the right edge sits to the left of
			// its point instead
			const place = (d, value, dy) => {
				const w = Math.max(...nameLines(h.name).map((l) => l.length), value.length) * 7.2;
				const right = x(d.p) + 8 + w <= width;
				return { x: right ? x(d.p) + 8 : x(d.p) - 8, y: y(d.v) + dy, value, anchor: right ? "start" : "end" };
			};
			if (!second) {
				const last = h.pts[h.pts.length - 1];
				return last && place(last, fmt(last.v), 4);
			}
			// the first line keeps clear of every note; the next only of those
			// whose words run rightward, as its label does
			const rightNotes = noteList.filter((n) => k === 0 || !n.left).map((n) => periods.indexOf(n.p));
			const clear = (d) => {
				const lx = x(d.p) + 8, ly = y(d.v) - 4;
				return (
					rightNotes.every((i) => Math.abs(periods.indexOf(d.p) - i) > 2) &&
					placed.every((q) => Math.abs(q.x - lx) > 120 || Math.abs(q.y - ly) > 34)
				);
			};
			const best = [...h.pts].sort((a, b) => b.v - a.v).find(clear) ?? peakOf(h.pts);
			const extra = (nameLines(h.name).length - 1) * 15;
			const at = place(best, narrow ? `${fmt(best.v)}, ${edge(best.p)}` : `${fmt(best.v)} in ${periodName(best.p)}`, -4 - extra);
			placed.push(at);
			return at;
		});
	});
	// the field named once, above everything drawn around a spot chosen for
	// each topic (clear of the notes and Fox's labels)
	// (on a phone the 2020 note's wrapped words reach 2021, so race moves on a year)
	const FIELD_AT = { polrace: "2021", lgbtq: "2022", fouls: "2025-01" };
	const FIELD_AT_NARROW = { polrace: "2022" };
	const fieldLabel = $derived.by(() => {
		const want = (narrow && FIELD_AT_NARROW[topic]) || FIELD_AT[topic];
		const p = periods.includes(want) ? want : periods[Math.floor(periods.length / 3)];
		// everything drawn under the label's width (narrower type on a phone)
		const near = periods.filter((q) => Math.abs(x(q) - x(p)) < (narrow ? 40 : 75));
		const top = Math.max(
			...near.flatMap((q) => [...field, ...heroes].map((s) => s.pts.find((d) => d.p === q)?.v ?? 0))
		);
		// and never up among the notes' words
		const notesFoot = noteList.length ? M.top + 16 + 14 * 3 + 16 : 0;
		return { p, v: top, y: Math.max(y(top) - 8, notesFoot) };
	});

	// --- hover ----------------------------------------------------------------
	let hover = $state(null);
	function onMove(e) {
		const box = e.currentTarget.getBoundingClientRect();
		const px = e.clientX - box.left;
		let i = 0, d = Infinity;
		periods.forEach((p, k) => {
			const dist = Math.abs(x(p) - px);
			if (dist < d) (d = dist), (i = k);
		});
		const p = periods[i];
		const rows = [
			...heroes.map((h) => ({ name: second ? h.name : FOX, v: valueOf(h.t, FOX, p), hi: true })),
			...(withField ? others : []).map((o) => ({ name: SHORT[o] ?? o, v: valueOf(topic, o, p) }))
		].filter((r) => r.v != null);
		rows.sort((a, b) => (b.hi === true) - (a.hi === true) || b.v - a.v);
		hover = { p, px: x(p), rows };
	}

	// --- each outlet, small ----------------------------------------------------
	const SW = 200, SH = 70, SM = { t: 4, r: 4, b: 14, l: 4 };
	const sx = scalePoint().domain(periods).range([SM.l, SW - SM.r]);
	const sy = scaleLinear().domain([0, yMax]).range([SH - SM.b, SM.t]);
	const spath = d3line().x((d) => sx(d.p)).y((d) => sy(d.v));
	const sarea = d3area().x((d) => sx(d.p)).y0(sy(0)).y1((d) => sy(d.v));

	const what = monthly
		? "articles each month"
		: "share of each outlet’s WNBA articles";
	const words = wordGroupsFor(topic, second).map((g, i) => ({ ...g, label: or(i ? list2Label : listLabel, g.label) }));
	// the line under the headline, as a Doc template: {swatch}, {swatch2} and
	// {grey} are the key's colour chips
	const swatch = (c) => `<span class="sw" style="background:${c}"></span>`;
	const dekDefault = second
		? `Fox News WNBA articles each month that use {swatch}<b>${NAME[topic]}</b>${NAME[topic].includes(" or ") ? ", or" : " or"} {swatch2}<b>${NAME[second]}</b>.` +
			(withField ? ` In grey, each other outlet’s articles with ${NAME[topic]}.` : "")
		: `Share of each outlet’s WNBA articles that mention ${NAME[topic]}, by ${monthly ? "month" : "year"}. {swatch}<b>Fox News</b> and {grey}${others.length === 6 ? "six" : others.length} other outlets.`;
	const dek = fill(or(subtitle, dekDefault), {
		swatch: swatch(COLOR[topic]),
		swatch2: second ? swatch(COLOR[second]) : "",
		grey: '<span class="sw grey"></span>'
	});
</script>

<figure class="fvf" bind:clientWidth={width}>
	<p class="kicker" style:color={COLOR[topic]}>{kicker || KICKER[topic] || ""}</p>
	{#if title}<h4 class="hed">{@html title}</h4>{/if}
	<p class="dek">
		{@html dek}
	</p>

	<div class="main">
		<svg {width} height={H} role="img" aria-label="{title || what}, Fox News against {others.length} other outlets">
			<!-- gridlines, the top one carrying the unit -->
			{#each yTicks as t, i (t)}
				{#if t > 0}
					<line class="grid" x1={M.left} x2={width - M.right + 10} y1={y(t)} y2={y(t)} />
					<text class="gtext" x={M.left} y={y(t) - 5}>{fmt(t)}{i === yTicks.length - 1 ? " " + or(unit, counts ? "articles" : "of articles") : ""}</text>
				{/if}
			{/each}
			<line class="base" x1={M.left} x2={width - M.right + 10} y1={y(0)} y2={y(0)} />
			{#each periods as p, i (p)}
				{@const lab = xLabel(p, i)}
				{#if lab}<text class="xtext" x={x(p)} y={H - 8} text-anchor="middle">{lab}</text>{/if}
			{/each}

			<!-- the dated notes -->
			{#each noteList as n (n.p + n.text)}
				{@const nx = x(n.p)}
				{@const tx = nx + (n.left ? -6 : 6)}
				<line class="note-line" x1={nx} x2={nx} y1={M.top - 4} y2={y(0)} />
				<text class="note" x={tx} y={M.top + 16} text-anchor={n.left ? "end" : "start"}>
					<tspan class="note-head" x={tx}>{n.head}</tspan>
					{#each wrap(narrow && n.short ? n.short : n.text, narrow ? 13 : 22) as l, k (k)}<tspan x={tx} dy="14">{l}</tspan>{/each}
				</text>
			{/each}

			<!-- the field, grey, named once -->
			{#each field as f (f.o)}
				<path class="field" d={path(f.pts)} />
			{/each}
			<!-- on a phone the two-line chart is too tight for labels on the lines:
			     the line under the headline names them, with their colours -->
			{#if withField && fieldLabel && !(narrow && second)}
				<text class="field-label" x={x(fieldLabel.p)} y={fieldLabel.y} text-anchor="middle">{or(fieldName, `Other outlets${second ? `’ ${NAME[topic]}` : ""}`)}</text>
			{/if}

			<!-- Fox, in colour, named where its line is -->
			{#each heroes as h, k (h.t)}
				<path class="hero" d={path(h.pts)} stroke={h.color} />
				{#if !monthly}
					{#each h.pts as d (d.p)}
						<circle class="hero-dot" cx={x(d.p)} cy={y(d.v)} r="4" fill={h.color} />
					{/each}
				{/if}
				{#if heroLabels[k] && !(narrow && second)}
					<text class="hero-label" x={heroLabels[k].x} y={heroLabels[k].y} fill={h.color} text-anchor={heroLabels[k].anchor}>
						{#each nameLines(h.name) as l, j (j)}<tspan x={heroLabels[k].x} dy={j ? 15 : 0}>{l}</tspan>{/each}
						<tspan class="hero-value" x={heroLabels[k].x} dy="15">{heroLabels[k].value}</tspan>
					</text>
				{/if}
			{/each}

			<!-- the fouls words where each was used most, in the line's colour -->
			{#each wordPeaks as w (w.p)}
				{@const px = x(w.p)}
				{@const left = px > width * 0.72}
				{@const lx = px + (left ? -9 : 9)}
				<text class="word-label" x={lx} y={y(w.v) - (w.words.length - 1) * 7.5 + 4} fill={COLOR[topic]} text-anchor={left ? "end" : "start"}>
					{#each w.words as t, j (t.term)}<tspan x={lx} dy={j ? 15 : 0}><tspan class="word-term">{t.term}</tspan> {t.k}</tspan>{/each}
				</text>
			{/each}

			{#if hover}
				<line class="cross" x1={hover.px} x2={hover.px} y1={M.top - 4} y2={y(0)} />
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
			<div class="tip" style:left="{Math.min(width - 190, Math.max(0, hover.px + (hover.px > width / 2 ? -190 : 14)))}px" style:top="{M.top}px">
				<p class="tip-t">{periodName(hover.p)}</p>
				{#each hover.rows as r (r.name)}
					<p class="tip-row" class:hi={r.hi}><span>{r.name}</span><span>{fmt(r.v)}</span></p>
				{/each}
			</div>
		{/if}
	</div>

	<!-- each outlet on its own, small, on the same scale -->
	<div class="strip">
		{#each outlets as o (o)}
			{@const fox = o === FOX}
			<div class="sm">
				<p class="sm-name">
					<span>{o}</span>
					<!-- the share across all years; no totals where the panels count
					     articles (fouls), as the lines show them -->
					{#if !counts}<span>{fmt(overall(topic, o))}</span>{/if}
				</p>
				<svg viewBox="0 0 {SW} {SH}" role="img" aria-label="{o}: {what}">
					<line class="sm-base" x1={SM.l} x2={SW - SM.r} y1={sy(0)} y2={sy(0)} />
					{#each [topic, ...(second ? [second] : [])] as t, k (t)}
						{@const pts = series(t, o)}
						{#if !second}<path class="sm-area" d={sarea(pts)} fill={fox ? COLOR[t] : "#8d877e"} />{/if}
						<path class="sm-line" d={spath(pts)} stroke={fox ? COLOR[t] : k ? "#c9c3ba" : "#a39a8d"} />
					{/each}
					<text class="sm-tick" x={SM.l} y={SH - 2}>{edge(periods[0])}</text>
					<text class="sm-tick" x={SW - SM.r} y={SH - 2} text-anchor="end">{edge(periods[periods.length - 1])}</text>
				</svg>
			</div>
		{/each}
	</div>

	<!-- the words counted -->
	<div class="source">
		{#each words as g (g.label)}
			<p><b>{g.label}:</b> {g.words.join(", ")}</p>
		{/each}
		<p>{@html or(sourceNote, "An article counts once, however often it uses them.")}</p>
	</div>
</figure>

<style>
	.fvf {
		margin: 0 0 8px;
		font-family: var(--font-graphic);
		color: var(--color-ink-dark);
	}
	.kicker {
		margin: 0 0 6px;
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
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
		font-size: 15px;
		line-height: 1.45;
		color: #4a4a4a;
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
		background: #c7c2b9;
	}
	.main {
		position: relative;
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
		stroke: var(--color-ink-dark);
		stroke-width: 1;
	}
	.field {
		fill: none;
		stroke: #c7c2b9;
		stroke-width: 1.25px;
	}
	.field-label {
		fill: #727272;
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
		fill: var(--color-ink-dark);
	}
	.cross {
		stroke: var(--color-ink-dark);
		stroke-width: 1;
	}
	.tip {
		position: absolute;
		z-index: 4;
		width: 180px;
		padding: 8px 10px;
		background: #fff;
		border: 1px solid #e2e2e2;
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
		margin-bottom: 4px !important;
	}
	.tip-row {
		display: flex;
		justify-content: space-between;
		gap: 14px;
		line-height: 1.5;
		color: #4a4a4a;
	}
	.tip-row.hi {
		color: var(--color-ink-dark);
		font-weight: 700;
	}
	.tip-row span:last-child {
		font-variant-numeric: tabular-nums;
	}
	.strip {
		margin-top: 30px;
		display: grid;
		grid-template-columns: repeat(4, minmax(0, 1fr));
		gap: 16px 18px;
	}
	.sm-name {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		gap: 6px;
		margin: 0 0 2px;
		font-size: 13px;
		font-weight: 700;
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
