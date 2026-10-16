<script>
	// Mirrored horizontal bars for a fightin'-words contrast
	import { base } from "$app/paths";
	import { LOGO_WIDTH, LOGO_RATIO } from "$utils/outlets.js";
	import { properCase } from "$utils/properCase.js";
	let {
		source = null,
		highlight = null,
		top = 12,
		// more: rank the list further than `top`, a page of `top` at a time
		// with Previous / Next under the bars, the frame the same height
		// (2026-10-01; it scrolled before)
		more = 0,
		// pager: show Previous / Next (a scrolly keeps it for its explore step)
		pager = true,
		example = null,
		// labels: "on" (the word on its bar), "beside" (a column of words down
		// the middle, the bars growing outward from it), "outside" (the bars
		// grow from the middle, the words in a column past their ends) or
		// "tip" (each word hugging the end of its bar, scores in the tooltip)
		labels = "on",
		// scale: "linear" (bar length is the score), "sqrt" (square-root, so a
		// runaway word does not squash the rest) or "cap" (the longest bar is
		// cut with a break mark at 1.2× the next longest)
		scale = "linear",
		// caps: true — words in capitals; "title" — first letter capitalised
		caps = false,
		// scores: true — the score printed past each bar (it is always in the
		// tooltip)
		scores = false,
		onhover = null,
		fill = false,
		// the name of the bottom side in the tooltip's counts ("others", "ESPN")
		otherName = "Others",
		// the top side's short name ("Fox", or "conservative media" for the pair)
		topName = "Fox",
		// note: the line under the chart — left out for the stock one, written
		// for your own (HTML allowed), present but blank for none
		note = undefined,
		// noteKind: "source" sets the note as a source line (small, left, over
		// a thin rule), as the main chart's caption is (2026-10-02)
		noteKind = "",
		// the Doc's words for the pager and the hover counts (fill.js slots)
		previous = "",
		next = "",
		range = "",
		hoverCounts = ""
	} = $props();
	const noteMode = $derived(note === undefined || note === null ? "stock" : String(note).trim() ? "custom" : "none");

	import { fill as fillIn, or } from "$utils/fill.js";
	const FOX = "var(--color-fox-navy)";
	const OTHERS = "var(--color-outlets)";
	const INK = "var(--color-ink)";
	const WEAK_Z = 1.96; // below this a word's lean is within noise

	let lit = $derived(new Set((highlight ?? []).map((w) => w.toLowerCase())));
	let anyLit = $derived(lit.size > 0);

	// pixel-true: the frame is measured, the drawing fills it
	let el = $state(null);
	let frame = $state({ w: 0 });
	let narrow = $derived(frame.w > 0 && frame.w < 640);
	let WIDTH = $derived(frame.w || 900);
	// fill: the scrolly asks the rows to stretch down the viewport, so a
	// chart with fifteen bars uses the screen instead of a strip of it
	let avail = $state(0);
	// room left under the bars for what sits below them (the pager, the note),
	// measured, so a two-line note under a pager is never cut off the screen
	let belowEl = $state(null);
	let pagerEl = $state(null);
	const reserve = () => 24 + (belowEl?.offsetHeight ?? 0) + (pagerEl?.offsetHeight ?? 0);
	$effect(() => {
		if (!fill || !el) return;
		rows;
		// measured against the sticky frame, not the viewport, so it holds
		// whether or not the chart is pinned on screen right now
		const measure = () => {
			const sticky = el.closest(".sticky");
			const er = el.getBoundingClientRect();
			if (sticky) {
				const sr = sticky.getBoundingClientRect();
				avail = sr.height - (er.top - sr.top) - reserve();
			} else {
				avail = window.innerHeight - er.top - reserve();
			}
		};
		measure();
		window.addEventListener("resize", measure);
		// the controls above the chart come and go with the step
		const ro = typeof ResizeObserver !== "undefined" ? new ResizeObserver(measure) : null;
		ro?.observe(el.parentElement ?? el);
		if (belowEl) ro?.observe(belowEl);
		return () => {
			window.removeEventListener("resize", measure);
			ro?.disconnect();
		};
	});
	const TOP = 34;
	const BOTTOM = 10;
	const ROW_MIN = 26,
		ROW_MAX = 44;
	let ROW = $derived(
		fill && avail > 0
			? Math.max(ROW_MIN, Math.min(ROW_MAX, (avail - TOP - BOTTOM) / viewRows))
			: ROW_MIN
	);
	let height = $derived(TOP + rows * ROW + BOTTOM);
	// each side's strongest words, highlighted ones kept even when they rank lower
	const side = (sign) =>
		(source?.points ?? [])
			.filter((p) => Math.sign(p.z) === sign)
			.sort((a, b) => Math.abs(b.z) - Math.abs(a.z));
	let fox = $derived(pick(side(1), 1));
	let others = $derived(pick(side(-1), -1));
	// with room to spare the chart shows more words rather than taller bars:
	// as many rows as fit at a comfortable height, up to a ceiling
	const ROW_COMFY = 32,
		TOP_MAX = 28;
	let topN = $derived(
		fill && avail > 0
			? Math.max(top, Math.min(TOP_MAX, Math.floor((avail - TOP - BOTTOM) / ROW_COMFY)))
			: top
	);
	let paged = $derived(more > topN);
	let page = $state(0);
	// the words ranked on each side, up to `more`, and how many pages they fill
	let ranked = $derived(Math.min(more, Math.max(side(1).length, side(-1).length)));
	let pages = $derived(paged ? Math.max(1, Math.ceil(ranked / topN)) : 1);
	// a highlighted word that isn't on the page showing: it stays at its real
	// rank, but the page gives up its last rows for a "⋯" and a row for it
	// ("#38"), so the reader sees it without the order being changed
	// (2026-10-02). The page keeps its height.
	let pins = $derived.by(() => {
		const none = { 1: [], [-1]: [], rows: 0, keep: topN };
		if (!paged || !anyLit) return none;
		const ranked = { 1: side(1).map((p, i) => ({ ...p, rank: i + 1 })), [-1]: side(-1).map((p, i) => ({ ...p, rank: i + 1 })) };
		let keep = topN, out = none;
		// the rows given up can uncover more highlighted words: settle it
		for (let pass = 0; pass < 4; pass++) {
			const res = { rows: 0, keep };
			for (const s of [1, -1]) {
				const shown = new Set(ranked[s].slice(page * topN, page * topN + keep).map((p) => p.word.toLowerCase()));
				res[s] = ranked[s].filter((p) => lit.has(p.word.toLowerCase()) && !shown.has(p.word.toLowerCase())).map((p) => ({ ...p, pin: true }));
			}
			res.rows = Math.max(res[1].length, res[-1].length);
			const next = res.rows ? Math.max(1, topN - res.rows - 1) : topN;
			out = res;
			if (next === keep) break;
			keep = next;
		}
		out.keep = keep;
		return out;
	});
	function pick(list, sign = 0) {
		if (paged)
			return [
				...list.slice(0, more).slice(page * topN, page * topN + pins.keep),
				...(sign ? pins[sign] : [])
			];
		const kept = list.slice(0, topN);
		for (const p of list.slice(topN))
			if (lit.has(p.word.toLowerCase())) kept.push(p);
		return kept;
	}
	// every page is a full page tall, so the chart does not jump
	let rows = $derived(paged ? topN : Math.max(fox.length, others.length, 1));
	let viewRows = $derived(rows);
	// a new comparison starts back on the first page
	$effect(() => {
		source;
		page = 0;
	});
	$effect(() => {
		if (page > pages - 1) page = pages - 1;
	});

	let GAP = $derived(narrow ? 4 : 10); // either side of the middle
	let beside = $derived(String(labels).trim().toLowerCase() === "beside");
	let outside = $derived(String(labels).trim().toLowerCase() === "outside");
	let tip_ = $derived(String(labels).trim().toLowerCase() === "tip");
	let mid = $derived(WIDTH / 2);
	// a column head can carry the outlet's wordmark on its outer side ("← [logo]
	// in ESPN", "in Fox News [logo] →"): source.topLogo /
	// source.bottomLogo name a file in static/logos (2026-09-29)
	// a logo's height in the head: a long wordmark (the Times, the Post) a
	// little shorter so it does not dwarf the words; its width from its shape
	const logoHeight = (file) => ((LOGO_RATIO[file] ?? 3) > 5 ? 12 : 15);
	const logoWidth = (file) =>
		file
			? LOGO_RATIO[file]
				? LOGO_RATIO[file] * logoHeight(file)
				: ((LOGO_WIDTH[file] ?? 40) * 15) / (file.endsWith(".png") ? 15 : 12)
			: 0;
	let topIn = $state(null);
	let topInWidth = $state(80);
	let bottomIn = $state(null);
	let bottomInWidth = $state(60);
	$effect(() => {
		source?.bottomLogo;
		source?.bottomShort;
		if (bottomIn) bottomInWidth = bottomIn.getComputedTextLength();
	});
	$effect(() => {
		source?.topLogo;
		source?.topShort;
		if (topIn) topInWidth = topIn.getComputedTextLength();
	});
	// a phone gets the square-root scale unless the Doc asked for another, so
	// the bars spread across the little width they have
	const scaleMode = $derived.by(() => {
		const m = String(scale).trim().toLowerCase();
		return narrow && (!m || m === "linear") ? "sqrt" : m;
	});
	let showScores = $derived(scores === true || String(scores) === "true");
	// paged, every page keeps the first page's scale: word 43's bar stays
	// shorter than word 1's instead of filling the width again
	let zs = $derived(
		(paged ? [...side(1).slice(0, more), ...side(-1).slice(0, more)] : [...fox, ...others])
			.map((p) => Math.abs(p.z))
			.sort((a, b) => b - a)
	);
	let capZ = $derived(scaleMode === "cap" && zs.length > 1 ? zs[1] * 1.2 : Infinity);
	let maxZ = $derived(Math.max(1, Math.min(zs[0] ?? 1, capZ)));
	const shape = (z) => (scaleMode === "sqrt" ? Math.sqrt(z) : z);
	// team names always in capitals (utils/properCase.js), then the caps setting
	const wordCase = (w) =>
		caps === true || String(caps) === "true"
			? w.toUpperCase()
			: String(caps).toLowerCase() === "title"
				? w.replace(/(^|[\s-])([a-z])/g, (m, a, b) => a + b.toUpperCase())
				: properCase(w);
	// bar length: leaves room past the end for a word that does not fit inside
	// outside: the bars keep the middle, the words take the outer column, with
	// room for the score between them
	// the room kept past the longest bar: for a score, a word beyond a short
	// bar, or just a margin
	let span = $derived(
		mid - GAP - LABEL -
			(showScores
				? narrow ? 60 : beside || outside ? 44 : 110
				: beside || outside || tip_
					? narrow ? 6 : 30
					: narrow ? 8 : 80)
	);
	// with the words at the bar tips, no score is drawn on the chart
	let len = $derived((z) => (shape(Math.min(Math.abs(z), capZ)) / shape(maxZ)) * span);
	const capped = (z) => Math.abs(z) > capZ;
	const yOf = (i) => TOP + i * ROW + ROW / 2;

	$effect(() => {
		if (!el) return;
		const measure = () => (frame = { w: Math.round(el.clientWidth) });
		measure();
		const ro = new ResizeObserver(measure);
		ro.observe(el);
		return () => ro.disconnect();
	});

	// the word goes inside its bar when it fits, else just past the bar's end
	let WORD_PX = $derived(narrow ? 12 : 13.5);
	let measureCtx = null;
	let chartFont = null;
	function textWidth(word) {
		if (typeof document === "undefined") return word.length * WORD_PX * 0.6;
		if (!measureCtx)
			measureCtx = document.createElement("canvas").getContext("2d");
		// a canvas cannot read a CSS variable: resolve the chart face once
		// (an unreadable font string would silently fall back to 10px sans)
		if (!chartFont)
			chartFont =
				getComputedStyle(document.documentElement).getPropertyValue("--font-chart").trim() ||
				'"Helvetica Neue", Helvetica, Arial, sans-serif';
		measureCtx.font = `700 ${WORD_PX}px ${chartFont}`;
		return measureCtx.measureText(word).width;
	}
	// the word column, when the words sit beside the bars: as wide as the
	// longest word shown, within reason
	let LABEL = $derived(
		beside || outside
			? Math.min(narrow ? 110 : 180, Math.max(narrow ? 70 : 100,
					...[...fox, ...others].map((p) => textWidth(p.word) + 14)))
			: 0
	);
	const fmt = (z) => Math.abs(z).toFixed(1);
	// a word's count with thousands commas ("1,234"); anything not a number as it came
	const count = (n) =>
		n != null && n !== "" && Number.isFinite(+n) ? (+n).toLocaleString("en-US") : n;
	// the width the bars reach, both sides (the longest bar and its word), so
	// the note under the chart wraps to the drawing rather than the frame
	// how far the bars (and their words) reach from the middle, either side,
	// over every page, so the heads and the caption hold still as the reader
	// pages through (the longest bar is on the first page)
	let barsReach = $derived.by(() => {
		let reach = 0;
		const all = paged ? [...side(1).slice(0, more), ...side(-1).slice(0, more)] : [...fox, ...others];
		for (const p of all) reach = Math.max(reach, LABEL + Math.max(len(p.z), textWidth(wordCase(p.word)) + 14));
		return Math.min(WIDTH / 2, GAP + reach);
	});
	// and no wider than 520px, so it reads as a caption, not a banner
	let plotWidth = $derived(Math.round(Math.min(WIDTH, 520, 2 * barsReach)));

	// the example on hover, as on the scatter: the word's sentence with the
	// form it took marked
	let hovered = $state(null);
	// a tap shows a bar's card and nothing on touch hides it: a click anywhere
	// outside the bars takes it away
	function clickAway(event) {
		if (!event.target.closest?.(".word-bars .bar")) hovered = null;
	}
	const escapeHtml = (s) =>
		s.replace(
			/[&<>"']/g,
			(c) =>
				({
					"&": "&amp;",
					"<": "&lt;",
					">": "&gt;",
					'"': "&quot;",
					"'": "&#39;"
				})[c]
		);
	// the stored example is the sentence with its neighbours on either side, so
	// the word it is an example of sits in the middle: when the word occurs more
	// than once ("the 2023 draft … No. 1 draft pick Caitlin Clark"), the
	// occurrence nearest the middle is the one meant
	function nearestMatch(text, rx) {
		const g = new RegExp(rx.source, rx.flags.includes("g") ? rx.flags : rx.flags + "g");
		let best = null;
		for (const m of text.matchAll(g)) {
			if (!best || Math.abs(m.index - text.length / 2) < Math.abs(best.index - text.length / 2)) best = m;
		}
		return best;
	}
	const esc = (w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
	const wordRx = (word, form) => {
		const stem = esc(word.length > 4 ? word.slice(0, -1) : word);
		return new RegExp(`\\b(?:${esc(form ?? word)}|${stem}\\w*)\\b`, "i");
	};
	function excerpt(sentence, word, form) {
		const MAX = 170;
		if (sentence.length <= MAX) return sentence;
		const m = nearestMatch(sentence, wordRx(word, form));
		const at = m ? m.index : 0;
		const start = Math.max(0, Math.min(at - 90, sentence.length - MAX));
		let cut = sentence.slice(start, start + MAX);
		if (start > 0) cut = "…" + cut.replace(/^\S*\s/, "");
		if (start + MAX < sentence.length) cut = cut.replace(/\s\S*$/, "") + "…";
		return cut;
	}
	function markWord(sentence, word, form, color) {
		const safe = escapeHtml(excerpt(sentence, word, form));
		const m = nearestMatch(safe, wordRx(word, form));
		if (!m) return safe;
		return safe.slice(0, m.index) +
			`<mark style="background:${color}2e;box-shadow:inset 0 -2px 0 ${color}66;` +
			`color:inherit;padding:0 1px;">${m[0]}</mark>` + safe.slice(m.index + m[0].length);
	}
	let tip = $derived.by(() => {
		if (!hovered) return null;
		for (const [list, sign] of [
			[fox, 1],
			[others, -1]
		]) {
			const i = list.findIndex((p) => p.word === hovered);
			if (i < 0) continue;
			const p = list[i];
			const w = Math.max(len(p.z), textWidth(p.word) + 14);
			// the card is anchored to the bar itself: over its middle, an arrow
			// pointing down at it; below the bar only when the screen has no
			// room above, and slid sideways to stay inside the frame
			const x = sign > 0 ? mid + GAP + w / 2 : mid - GAP - w / 2;
			// the example, with the outlet it came from (a player chart's
			// stored example says so itself; otherwise the side is enough)
			const eg = p.eg
				? { s: p.eg, w: p.egw, o: p.ego ?? (sign > 0 ? (topName === "Fox" ? "Fox News" : topName) : "the other outlets") }
				: (example?.(p.word, p.z) ?? null);
			return { p, sign, y: yOf(i), x, eg };
		}
		return null;
	});
	// the card's own size, measured once it renders, places it
	let cardW = $state(320);
	let cardH = $state(120);
	const ARROW = 9; // the pointer's height, and the gap it makes
	let tipBox = $derived.by(() => {
		if (!tip) return null;
		const left = Math.max(0, Math.min(WIDTH - cardW, tip.x - cardW / 2));
		// room above is measured on the screen, not in the frame: the chart
		// sits in a sticky box, so the frame's top may be off the screen
		const frameTop = el?.getBoundingClientRect().top ?? 0;
		const above = frameTop + tip.y - ROW / 2 - ARROW - cardH >= 4;
		return {
			left,
			top: above ? tip.y - ROW / 2 - ARROW - cardH : tip.y + ROW / 2 + ARROW,
			above,
			// the arrow stays on the bar even when the card has been slid
			arrow: Math.max(14, Math.min(cardW - 14, tip.x - left))
		};
	});
</script>

<svelte:window onclick={clickAway} />

<div class="word-bars" bind:this={el}>
	{#if source}
		<!-- the column heads -->
		<svg width={WIDTH} height={TOP - 24} viewBox="0 0 {WIDTH} {TOP - 24}" role="presentation">
			{#if source.topHead}
				<!-- heads at the bars' outer edges, saying what each side means:
				     "← Other outlets use more" · "Fox News uses more →" (2026-10-02) -->
				{@const oneLine = textWidth(source.bottomHead) + textWidth(source.topHead) + 60 < 2 * barsReach}
				{#if oneLine}
					<text class="head edge others" x={0} y="10" text-anchor="start">← {source.bottomHead}</text>
					<text class="head edge fox" x={WIDTH} y="10" text-anchor="end">{source.topHead} →</text>
				{:else}
					<!-- too narrow for both on one line: each breaks before "use(s) more" -->
					{@const split = (t) => { const i = t.search(/ uses? more$/); return i > 0 ? [t.slice(0, i), t.slice(i + 1)] : [t, ""]; }}
					<text class="head edge narrow others" x={mid - barsReach} y="11" text-anchor="start"
						><tspan x={mid - barsReach}>← {split(source.bottomHead)[0]}</tspan><tspan x={mid - barsReach} dy="13">{split(source.bottomHead)[1]}</tspan></text
					>
					<text class="head edge narrow fox" x={mid + barsReach} y="11" text-anchor="end"
						><tspan x={mid + barsReach}>{split(source.topHead)[0]} →</tspan><tspan x={mid + barsReach} dy="13">{split(source.topHead)[1]}</tspan></text
					>
				{/if}
			{:else if source.bottomLogo}
				<!-- mirrored: "← [logo] in ESPN", the wordmark on the outer side -->
				{@const w = logoWidth(source.bottomLogo)}
				<text class="head others" x={mid - GAP} y="16" text-anchor="end" bind:this={bottomIn}
					>{source.bottomShort}</text
				>
				<image
					href="{base}/logos/{source.bottomLogo}"
					x={mid - GAP - bottomInWidth - 6 - w}
					y={16 - logoHeight(source.bottomLogo) + 2 - (15 - logoHeight(source.bottomLogo)) / 2}
					width={w}
					height={logoHeight(source.bottomLogo)}
					preserveAspectRatio="xMaxYMid meet"
				><title>{source.bottomShort}</title></image>
				<text class="head others" x={mid - GAP - bottomInWidth - 6 - w - 6} y="16" text-anchor="end">←</text>
			{:else}
				<text class="head others" x={mid - GAP} y="16" text-anchor="end"
					>← {source.bottomShort ?? "everyone else"}</text
				>
			{/if}
			{#if source.topHead}
				<!-- drawn above, with the other side's -->
			{:else if source.topLogo}
				{@const w = logoWidth(source.topLogo)}
				<text class="head fox" x={mid + GAP} y="16" text-anchor="start" bind:this={topIn}>{source.topShort}</text>
				<image
					href="{base}/logos/{source.topLogo}"
					x={mid + GAP + topInWidth + 6}
					y={16 - logoHeight(source.topLogo) + 2 - (15 - logoHeight(source.topLogo)) / 2}
					width={w}
					height={logoHeight(source.topLogo)}
					preserveAspectRatio="xMinYMid meet"
				><title>{source.topShort}</title></image>
				<text class="head fox" x={mid + GAP + topInWidth + 6 + w + 6} y="16" text-anchor="start">→</text>
			{:else}
				<text class="head fox" x={mid + GAP} y="16" text-anchor="start"
					>{source.topShort ?? "in Fox News"} →</text
				>
			{/if}
		</svg>
		<svg
			width={WIDTH}
			height={height - TOP + 6}
			viewBox="0 {TOP - 6} {WIDTH} {height - TOP + 6}"
			onmouseleave={() => (hovered = null)}
			role="presentation"
		>
			<line class="axis" x1={mid} x2={mid} y1={TOP - 6} y2={height - BOTTOM} />

			{#each [[fox, 1], [others, -1]] as [list, sign]}
				{#if pins.rows && pins[sign].length}
					<!-- the gap between the page and the pinned words -->
					<text class="pin-gap" x={mid + sign * (GAP + LABEL + 10)} y={yOf(pins.keep) + 4} text-anchor={sign > 0 ? "start" : "end"}>⋯</text>
				{/if}
				{#each list as p, i (p.word)}
					{@const y = yOf(p.pin ? i + 1 : i)}
					{@const w = len(p.z)}
					{@const on = !anyLit || lit.has(p.word.toLowerCase())}
					{@const weak = Math.abs(p.z) < WEAK_Z}
					{@const color = sign > 0 ? FOX : OTHERS}
					<!-- a label too long for its half (three-word phrases on a phone)
					     shrinks just enough to fit, down to 9px -->
					{@const room = mid - GAP - (beside || outside ? 0 : LABEL) - 18}
					{@const tw0 = textWidth(wordCase(p.word))}
					{@const fs = tw0 > room ? Math.max(9, (WORD_PX * room) / tw0) : WORD_PX}
					{@const tw = (tw0 * fs) / WORD_PX}
					{@const over = tw + 14 - w}
					<!-- a word that overhangs its bar by a hair slides in by that much -->
					{@const nudge = !beside && !outside && !tip_ && over > 0 && over <= 7 ? over : 0}
					{@const inside = !beside && !outside && !tip_ && over <= 7}
					{@const foot = sign > 0 ? mid + GAP + (outside ? 0 : LABEL) : mid - GAP - (outside ? 0 : LABEL)}
					{@const end = sign > 0 ? foot + w : foot - w}
					{@const reach =
						beside || outside
							? end
							: sign > 0
								? Math.max(end, foot + tw + 14)
								: Math.min(end, foot - tw - 14)}
					<g
						class="bar"
						class:dim={!on}
						class:weak
						class:hovered={hovered === p.word}
						onmouseenter={() => {
							hovered = p.word;
							onhover?.(p.word);
						}}
						onmouseleave={() => (hovered = null)}
						role="presentation"
					>
						<rect
							class="fill"
							x={sign > 0 ? foot : end}
							y={y - ROW * 0.36}
							width={w}
							height={ROW * 0.72}
							rx="3"
							fill={color}
						/>
						<!-- the word, white; past its bar's end it gets an outline in the
						     bar's colour so it still reads as the bar's label -->
						<text
							class="word"
							class:halo={!inside && !beside && !outside && !tip_}
							x={outside ? mid + sign * (GAP + span + 40) : beside ? mid + sign * GAP : tip_ ? end + sign * 7 : foot + sign * (7 - nudge)}
							y={y + 4.5}
							text-anchor={sign > 0 ? "start" : "end"}
							fill="#fff"
							style:--halo={color}
							font-size={fs}>{wordCase(p.word)}</text
						>
						{#if p.pin && (sign > 0 ? WIDTH - reach - 6 : reach - 6) >= String(p.rank).length * 7.5 + 10}
							<text class="pin-rank" x={reach + sign * 6} y={y + 4} text-anchor={sign > 0 ? "start" : "end"}>#{p.rank}</text>
						{/if}
						{#if capped(p.z)}
							<!-- a break mark: the bar runs past the frame's scale -->
							<path
								class="break"
								d="M{end - sign * 9},{y - ROW * 0.36 - 2} l{sign * 4},{ROW * 0.36} l{-sign * 4},{ROW * 0.36 + 2}"
							/>
						{/if}
						<!-- its score, past the bar or the word, whichever is longer
						     (with words at the tips the score stays in the tooltip) -->
						{#if showScores && !tip_}
						<text
							class="score"
							x={reach + sign * 6}
							y={y + 4}
							text-anchor={sign > 0 ? "start" : "end"}>{fmt(p.z)}</text
						>
						{/if}
					</g>
				{/each}
			{/each}
		</svg>
		{#if paged && pages > 1 && pager}
			<div class="pager" bind:this={pagerEl}>
				<button type="button" disabled={page === 0} onclick={() => (page -= 1)}>{or(previous, "← Previous")}</button>
				<span class="pager-range"
					>{fillIn(or(range, "{from}–{to} of {total}"), { from: page * topN + 1, to: Math.min(ranked, (page + 1) * topN), total: ranked })}</span
				>
				<button type="button" disabled={page >= pages - 1} onclick={() => (page += 1)}>{or(next, "Next →")}</button>
			</div>
		{/if}

		{#if tip}
			{@const color = tip.sign > 0 ? FOX : OTHERS}
			<div
				class="tip-card"
				bind:clientWidth={cardW}
				bind:clientHeight={cardH}
				class:below={!tipBox.above}
				style="left:{tipBox.left}px; top:{tipBox.top}px; --arrow:{tipBox.arrow}px"
			>
				<!-- the side's colour in a swatch and on the quote's rule; the words in ink -->
				<span class="tip-head">{properCase(tip.p.word)}</span>
				<span class="tip-count"
					>{fillIn(or(hoverCounts, "{top} {topCount} · {bottom} {bottomCount} · Score {score}"), {
						top: topName,
						bottom: otherName,
						topCount: count(tip.p.nf),
						bottomCount: count(tip.p.no),
						score: fmt(tip.p.z)
					})}{#if tip.p.pin} · #{tip.p.rank}{/if}</span
				>
				{#if tip.eg}
					<p style="border-left-color:{color}">
						{#if tip.eg.o}<span class="tip-source">{tip.eg.o}</span>{/if}
						{@html markWord(tip.eg.s, tip.p.word, tip.eg.w, color)}
					</p>
				{/if}
			</div>
		{/if}

		<!-- what sits under the bars, measured as one, so the bars leave it room -->
		<div class="below" bind:this={belowEl}>
			{#if noteMode === "custom"}
				<!-- a source line spans the bars, edge to edge with the heads above -->
				<p class="note" class:source={noteKind === "source"} style:max-width="{noteKind === "source" ? Math.round(2 * barsReach) : plotWidth}px">{@html note}</p>
			{:else if noteMode === "stock"}
				<p class="note" style:max-width="{plotWidth}px">
					Bars are each word's fightin'-words score. Faded bars score under {WEAK_Z},
					within noise. Hover a bar for an example.
				</p>
			{/if}
		</div>
	{/if}
</div>

<style>
	.word-bars {
		width: 100%;
		max-width: 720px;
		margin: 0 auto 5rem auto;
		position: relative;
	}
	svg {
		display: block;
		overflow: visible;
	}
	/* Previous / Next: small underlined links, so they don't pull the eye off the bars */
	.pager {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 12px;
		margin-top: 6px;
		font-family: var(--font-chart);
		font-size: 12px;
		color: var(--color-fg);
	}
	.pager button {
		appearance: none;
		border: 0;
		background: none;
		padding: 2px 0;
		color: var(--color-fg);
		font: inherit;
		text-decoration: underline;
		text-underline-offset: 2px;
		cursor: pointer;
	}
	.pager button:disabled {
		opacity: 0.3;
		text-decoration: none;
		cursor: not-allowed;
	}
	.pager-range {
		font-variant-numeric: tabular-nums;
		color: var(--wnba-tan-dark);
	}
	.head {
		font-family: var(--font-chart);
		text-transform: uppercase !important;
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 0.06em;
		text-transform: uppercase;
	}
	.head.fox {
		fill: var(--color-fox-navy);
		text-transform: uppercase;
		font-size: 12px;
	}
	/* the edge heads: sentence case, a little larger */
	.head.edge {
		text-transform: uppercase;
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 0;
		text-transform: none;
	}
	.head.edge.narrow {
		text-transform: uppercase;
		font-size: 12px;
	}
	.head.others {
		fill: var(--color-outlets);
		text-transform: uppercase;
		font-size: 12px;
	}
	.pin-gap {
		font-size: 16px;
		font-weight: 700;
		fill: rgba(42, 21, 3, 0.5);
	}
	.pin-rank {
		font-family: var(--font-sans);
		font-size: 12px;
		font-weight: 700;
		fill: rgba(42, 21, 3, 0.6);
	}
	.axis {
		stroke: var(--wnba-tan-dark);
		stroke-width: 1.5;
	}
	.break {
		fill: none;
		stroke: var(--color-paper, var(--color-paper));
		stroke-width: 3;
	}
	.bar .fill {
		opacity: 0.88;
		transition: opacity 250ms ease;
	}
	/* within noise: a lighter tint of the same colour, not a greyed-out one
	   (transparency over the orange page turns navy to mud) */
	.bar.weak .fill {
		opacity: 0.8;
		filter: brightness(1.45) saturate(0.85);
	}
	/* a bar outside the step's words fades, but its label stays legible */
	.bar.dim .fill {
		opacity: 0.22;
		filter: none;
	}
	.bar.dim .word,
	.bar.dim .score {
		opacity: 0.55;
	}
	.bar:hover .fill {
		opacity: 1;
	}
	/* the hovered (or tapped) bar's words at full strength, faded bar or not */
	.bar:hover .word,
	.bar:hover .score,
	.bar:hover .pin-rank,
	.bar.hovered .word,
	.bar.hovered .score,
	.bar.hovered .pin-rank {
		opacity: 1;
	}
	.word {
		font-family: var(--font-chart);
		font-weight: 700;
		pointer-events: none;
	}
	/* a word that runs past its bar keeps its white, with an outline in the
	   bar's own colour around the letters */
	.word.halo {
		paint-order: stroke;
		stroke: var(--halo);
		stroke-width: 3.5px;
		stroke-linejoin: round;
	}
	.score {
		font-family: var(--font-chart);
		font-size: 11px;
		font-weight: 600;
		fill: rgba(42, 21, 3, 0.6);
		pointer-events: none;
	}
	.tip-card {
		position: absolute;
		z-index: 8;
		pointer-events: none;
		width: 300px;
		max-width: 80vw;
		background: var(--color-white);
		border: 1px solid var(--color-rule);
		border-radius: 4px;
		padding: 0.75rem 1rem;
		box-shadow: 0 2px 10px rgba(0, 0, 0, 0.12);
		color: var(--color-fg);
		font-size: 12.5px;
		pointer-events: none;
	}
	/* the shared tooltip (variables.css) */
	.tip-head {
		display: block;
		font-size: 18px;
		font: var(--tip-title);
	}
	.tip-card .swatch {
		display: inline-block;
		width: 10px;
		height: 10px;
		border-radius: 2px;
		margin-right: 7px;
		vertical-align: 1px;
	}
	.tip-source {
		display: block;
		font: var(--tip-small);
		color: var(--wnba-tan-dark);
		margin-top: 4px;
	}
	.tip-count {
		display: block;
		font: var(--tip-small);
		color: var(--wnba-tan-dark);
		margin: 3px 0 0;
	}
	.tip-card p {
		margin: 9px 0 0;
		padding: 1px 0 1px 9px;
		border-left: 3px solid var(--tip-rule);
		font: var(--tip-quote);
		color: var(--color-fg);
	}
	/* the pointer: a paper triangle with the same hairline, at the bar */
	/* .tip-card::after,
	.tip-card::before {
		content: "";
		position: absolute;
		left: var(--arrow, 50%);
		transform: translateX(-50%);
		border: 8px solid transparent;
	}
	.tip-card::before {
		bottom: -17px;
		border-top-color: var(--tip-border);
	}
	.tip-card::after {
		bottom: -15px;
		border-top-color: var(--tip-bg);
	}
	.tip-card.below::before {
		bottom: auto;
		top: -17px;
		border-top-color: transparent;
		border-bottom-color: var(--tip-border);
	}
	.tip-card.below::after {
		bottom: auto;
		top: -15px;
		border-top-color: transparent;
		border-bottom-color: var(--tip-bg);
	} */
	.note {
		margin: 6px auto 0;
		font-size: 12px;
		color: var(--wnba-tan-dark);
		text-align: center;
	}
	.note.source {
		font-family: var(--font-sans);
		margin-top: 2rem;
		padding-top: 8px;
		border-top: 1px solid var(--color-rule);
		text-align: left;
		line-height: 1.5;
	}
</style>
