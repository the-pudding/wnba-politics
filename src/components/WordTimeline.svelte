<script>
	// How often a word turns up in Fox's WNBA articles, week by week (or day
	// by day), with a date marked.
	import data from "$data/word_timeline.json";

	let {
		word = "hip-check",
		words = "",
		// overlay: a second word (or group, added up) drawn as its own area on
		// top of the main series, in overlayColor, sharing the scale
		overlay = "",
		overlayLabel = "",
		overlayColor = "var(--color-fox-navy)",
		// overlayStack: the overlay sits on top of the main series, stacked,
		// rather than drawn over it
		overlayStack = false,
		outlet = "Fox News",
		scope = "any",
		scaleTo = "",
		chart = "lines",
		combine = false,
		color = "var(--color-fox)",
		label = "",
		scaleWords = "",
		xaxis = true,
		quiet = false,
		annotate = false,
		// the drawing's size in its own units (type stays the same size, so a
		// narrower drawing suits a small panel)
		width = 900,
		height = 300,
		// axis: false hides the y labels (a panel row shares them)
		axis = true,
		by = "week",
		from = "2024-01-01",
		to = "",
		mark = "",
		markLabel = ""
	} = $props();

	const DAY = 86400000;
	const parse = (s) => new Date(s + "T00:00:00Z");
	const iso = (d) => d.toISOString().slice(0, 10);
	const weekly = $derived(String(by).trim().toLowerCase() !== "day");
	// several words: lines on one plot, in a fixed colour order
	const PALETTE = ["var(--color-fox-navy)", "var(--color-outlets)", "var(--color-fox)", "var(--color-politics)", "var(--color-brown)", "var(--color-lgbtq)"];
	let source = $derived(data.outlets[String(outlet).trim()] ?? data.outlets["Fox News"]);
	let field = $derived(
		["headline", "mentions"].includes(String(scope).trim().toLowerCase())
			? String(scope).trim().toLowerCase()
			: "any"
	);
	let unit = $derived(field === "mentions" ? "mentions" : "articles");
	let list = $derived(
		String(words)
			.split(",")
			.map((w) => w.trim())
			.filter((w) => w && source.words[w])
	);
	const combined = combine === true || String(combine).trim().toLowerCase() === "true";
	let multi = $derived(list.length > 1 && !combined);
	let stacked = $derived(multi && String(chart).trim().toLowerCase() === "stacked");
	let area = $derived(!multi && String(chart).trim().toLowerCase() === "area");
	const entriesFor = (src) => {
		if (combined && list.length) {
			// one series: the articles that use any of the words, each counted
			// once (from the per-article bit-sets); mentions simply add up
			const counts = {}, examples = {};
			const order = src.order ?? [];
			const bits = list.reduce((m, w) => (order.includes(w) ? m | (1 << order.indexOf(w)) : m), 0);
			if (field === "mentions" || !bits) {
				for (const w of list) {
					const e = src.words[w] ?? { any: {}, headline: {}, examples: {} };
					for (const [day, n] of Object.entries(e[field] ?? {})) counts[day] = (counts[day] ?? 0) + n;
				}
			} else {
				const sets = field === "headline" ? (src.headMasks ?? {}) : (src.masks ?? {});
				for (const [day, arr] of Object.entries(sets)) {
					const n = arr.filter((m) => m & bits).length;
					if (n) counts[day] = n;
				}
			}
			for (const w of list)
				for (const [day, h] of Object.entries(src.words[w]?.examples ?? {})) examples[day] ??= h;
			return [{ word: String(label).trim() || list.join(", "), color, counts, examples }];
		}
		return (multi ? list : [String(word).trim()]).map((w, i) => {
			const e = src.words[w] ?? { any: {}, headline: {}, examples: {} };
			return { word: w, color: multi ? PALETTE[i % PALETTE.length] : color, counts: e[field] ?? {}, examples: e.examples ?? {} };
		});
	};
	let entries = $derived(entriesFor(source));
	let overlayList = $derived(
		String(overlay)
			.split(",")
			.map((w) => w.trim())
			.filter((w) => w && source.words[w])
	);
	// the overlay as one combined series (articles counted once), like `combine`
	const overlayFor = (src) => {
		if (!overlayList.length) return [];
		const counts = {}, examples = {};
		const order = src.order ?? [];
		const bits = overlayList.reduce((m, w) => (order.includes(w) ? m | (1 << order.indexOf(w)) : m), 0);
		if (field === "mentions" || !bits) {
			for (const w of overlayList) {
				const e = src.words[w] ?? { any: {}, headline: {}, examples: {} };
				for (const [day, n] of Object.entries(e[field] ?? {})) counts[day] = (counts[day] ?? 0) + n;
			}
		} else {
			const sets = field === "headline" ? (src.headMasks ?? {}) : (src.masks ?? {});
			for (const [day, arr] of Object.entries(sets)) {
				const n = arr.filter((m) => m & bits).length;
				if (n) counts[day] = n;
			}
		}
		for (const w of overlayList)
			for (const [day, h] of Object.entries(src.words[w]?.examples ?? {})) examples[day] ??= h;
		return [{ word: String(overlayLabel).trim() || overlayList.join(", "), color: overlayColor, counts, examples }];
	};
	let overlayEntries = $derived(overlayFor(source));
	const entry = $derived(entries[0]);
	let end = $derived(
		String(to).trim() || Object.keys(source.articles).sort().at(-1) || "2026-08-31"
	);
	// the bins: every day, or every Monday-to-Sunday week, from `from` to `to`
	const binsFor = (src, entries) => {
		const entry = entries[0];
		const start = parse(from);
		const last = parse(end);
		const out = [];
		if (weekly) {
			// back up to the Monday on or before the start
			const s = new Date(start);
			s.setUTCDate(s.getUTCDate() - ((s.getUTCDay() + 6) % 7));
			for (let d = s; d <= last; d = new Date(d.getTime() + 7 * DAY)) {
				let hits = 0, articles = 0, example = "";
				const each = entries.map(() => 0);
				for (let k = 0; k < 7; k++) {
					const key = iso(new Date(d.getTime() + k * DAY));
					hits += entry.counts[key] ?? 0;
					entries.forEach((e, j) => (each[j] += e.counts[key] ?? 0));
					articles += src.articles[key] ?? 0;
					if (!example && entry.examples[key]) example = entry.examples[key];
				}
				out.push({ start: iso(d), hits, each, articles, example });
			}
		} else {
			for (let d = start; d <= last; d = new Date(d.getTime() + DAY)) {
				const key = iso(d);
				out.push({
					start: key,
					hits: entry.counts[key] ?? 0,
					each: entries.map((e) => e.counts[key] ?? 0),
					articles: src.articles[key] ?? 0,
					example: entry.examples[key] ?? ""
				});
			}
		}
		return out;
	};
	let bins = $derived(binsFor(source, entries));
	// the y-axis: this outlet's peak, or another outlet's when `scaleTo` names one
	let scaleSource = $derived(data.outlets[String(scaleTo).trim()] ?? null);
	let scaleList = $derived(
		String(scaleWords)
			.split(",")
			.map((w) => w.trim())
			.filter((w) => w && source.words[w])
	);
	// the scale: another outlet's bins, and/or a set of words' bins, so rows
	// and panels compare
	let scaleBins = $derived.by(() => {
		const base = scaleSource ?? source;
		if (scaleList.length)
			return scaleList.flatMap((w) =>
				binsFor(base, [{ word: w, color, counts: base.words[w]?.[field] ?? {}, examples: {} }])
			);
		return scaleSource ? binsFor(scaleSource, entriesFor(scaleSource)) : null;
	});
	let overlayBins = $derived(overlayEntries.length ? binsFor(source, overlayEntries) : null);
	let overlayScaleBins = $derived(
		overlayEntries.length && scaleSource ? binsFor(scaleSource, overlayFor(scaleSource)) : null
	);
	const stackOn = $derived(overlayStack === true || String(overlayStack).trim().toLowerCase() === "true");
	let peak = $derived.by(() => {
		const main = scaleBins ?? bins;
		const over = overlayScaleBins ?? overlayBins;
		const values = main.flatMap((b, i) =>
			stacked ? [b.each.reduce((a, v) => a + v, 0)] : multi ? b.each : [b.hits + (stackOn && over?.[i] ? over[i].hits : 0)]
		);
		return Math.max(1, ...values, ...(stackOn ? [] : (over ?? []).map((b) => b.hits)));
	});
	let overlayTotal = $derived((overlayBins ?? []).reduce((s, b) => s + b.hits, 0));
	let total = $derived(bins.reduce((s, b) => s + b.hits, 0));
	let totals = $derived(entries.map((_, j) => bins.reduce((s, b) => s + b.each[j], 0)));
	// each line's path, and where to put its label (its peak)
	let lines = $derived(
		entries.map((e, j) => {
			const pts = bins.map((b, i) => [xOf(i) + stepX / 2, yOf(b.each[j])]);
			let top = 0;
			bins.forEach((b, i) => {
				if (b.each[j] > bins[top].each[j]) top = i;
			});
			// the label sits beside the peak, on whichever side has room
			const right = pts[top][0] > PAD.left + plotW * 0.7;
			return {
				...e,
				d: pts.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`).join(" "),
				label: {
					x: right ? pts[top][0] - 8 : pts[top][0] + 8,
					y: Math.max(PAD.top + 12, pts[top][1] + 4),
					anchor: right ? "end" : "start"
				}
			};
		})
	);

	// on a phone the drawing is scaled to the screen: drawn narrower there, so
	// the type comes out legible and the ticks thin to one a year
	let narrow = $state(false);
	$effect(() => {
		const mq = window.matchMedia("(max-width: 640px)");
		const set = () => (narrow = mq.matches);
		set();
		mq.addEventListener("change", set);
		return () => mq.removeEventListener("change", set);
	});
	const WIDTH = $derived(narrow ? Math.min(+width || 900, 460) : +width || 900);
	const HEIGHT = $derived(+height || 300);
	// a small panel: a tick a year, and no date label on the mark
	let small = $derived(WIDTH < 600);
	// room above the plot for the legend row (several words) or the total
	let PAD = $derived({
		top: quiet ? 10 : multi ? 34 : 26,
		right: 18,
		bottom: xaxis ? 42 : 14,
		left: axis ? 40 : 14
	});
	let plotW = $derived(WIDTH - PAD.left - PAD.right);
	let plotH = $derived(HEIGHT - PAD.top - PAD.bottom);
	let stepX = $derived(plotW / Math.max(1, bins.length));
	const xOf = (i) => PAD.left + i * stepX;
	const yOf = (v) => PAD.top + plotH - (v / peak) * plotH;
	// the mark: where the date falls among the bins
	let markX = $derived.by(() => {
		const m = String(mark).trim();
		if (!m) return null;
		const t = parse(m).getTime();
		const i = bins.findIndex(
			(b, j) => t >= parse(b.start).getTime() && (j === bins.length - 1 || t < parse(bins[j + 1].start).getTime())
		);
		if (i < 0) return null;
		const span = weekly ? 7 : 1;
		const frac = (t - parse(bins[i].start).getTime()) / (span * DAY);
		return xOf(i) + frac * stepX;
	});
	// a tick each quarter, labelled with the month and year
	let ticks = $derived(
		bins
			.map((b, i) => ({ b, i }))
			.filter(({ b }, k) => {
				const d = parse(b.start);
				const prev = k ? parse(bins[k - 1].start) : null;
				return !prev || d.getUTCMonth() !== prev.getUTCMonth();
			})
			.filter(({ b }) => (small ? [0] : [0, 3, 6, 9]).includes(parse(b.start).getUTCMonth()))
			.map(({ b, i }) => ({
				x: xOf(i),
				label: small
					? String(parse(b.start).getUTCFullYear())
					: parse(b.start).toLocaleDateString("en-US", { month: "short", year: "numeric", timeZone: "UTC" })
			}))
	);
	let yTicks = $derived([...new Set([0, Math.round(peak / 2), peak])]);
	// with a combined total: where each word peaks, its name on the line
	let notes = $derived.by(() => {
		if (!(combined && (annotate === true || String(annotate) === "true"))) return [];
		const out = [];
		for (const w of list) {
			const e = source.words[w] ?? {};
			const rows = binsFor(source, [{ word: w, color, counts: e[field] ?? {}, examples: {} }]);
			let top = 0;
			rows.forEach((b, i) => {
				if (b.hits > rows[top].hits) top = i;
			});
			if (!rows[top]?.hits) continue;
			// stacked under an overlay, the word's label clears the band on top of it
			const lift = stackOn && overlayBins?.[top] ? overlayBins[top].hits : 0;
			out.push({ word: w, i: top, x: xOf(top) + stepX / 2, y: yOf(bins[top].hits + lift), peak: rows[top].hits });
		}
		// a label sits above its peak; one that would run off the top, or sit
		// on the marked date, goes beside the spike instead, and labels that
		// share a spike stack downward there
		out.sort((a, b) => a.x - b.x);
		const mx = markX;
		let sideCount = 0;
		let lastX = -Infinity, lastY = 0;
		for (const n of out) {
			n.ly = n.y - 10;
			n.side = n.ly < PAD.top + 8 || (mx !== null && Math.abs(n.x - mx) < 40);
			if (!n.side && n.x - lastX < 70) n.ly = Math.min(n.ly, lastY - 14);
			if (n.side) {
				n.ly = Math.max(PAD.top + 14, n.y + 4) + sideCount * 14;
				n.lx = n.x - 10;
				sideCount++;
			} else {
				n.lx = n.x;
				lastX = n.x; lastY = n.ly;
			}
		}
		return out;
	});
	// one word as a line with its area shaded
	let areaPath = $derived.by(() => {
		if (!area) return null;
		const pts = bins.map((b, i) => [xOf(i) + stepX / 2, yOf(b.hits)]);
		const line = pts.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
		const base = PAD.top + plotH;
		return { line, fill: `${line} L${pts.at(-1)[0].toFixed(1)},${base} L${pts[0][0].toFixed(1)},${base} Z` };
	});

	// the overlay's area and line, and its label at its peak
	let overlayPath = $derived.by(() => {
		if (!overlayBins || !overlayBins.length) return null;
		// stacked: the band sits on the main series; otherwise it rises from the axis
		const under = (i) => (stackOn ? bins[i]?.hits ?? 0 : 0);
		const pts = overlayBins.map((b, i) => [xOf(i) + stepX / 2, yOf(under(i) + b.hits)]);
		const line = pts.map(([x, y], i) => `${i ? "L" : "M"}${x.toFixed(1)},${y.toFixed(1)}`).join(" ");
		const base = PAD.top + plotH;
		const floor = stackOn
			? overlayBins.map((_, i) => [xOf(i) + stepX / 2, yOf(under(i))]).reverse()
					.map(([x, y]) => `L${x.toFixed(1)},${y.toFixed(1)}`).join(" ")
			: `L${pts.at(-1)[0].toFixed(1)},${base} L${pts[0][0].toFixed(1)},${base}`;
		let top = 0;
		overlayBins.forEach((b, i) => {
			if (b.hits > overlayBins[top].hits) top = i;
		});
		// the label sits at the right edge, level with the band's top there
		const lastX = pts.at(-1)[0];
		const nearEnd = overlayBins.slice(-6);
		const endTop = Math.max(...nearEnd.map((b, k) => under(overlayBins.length - nearEnd.length + k) + b.hits));
		return {
			line,
			fill: `${line} ${floor} Z`,
			topOf: (i) => under(i) + (overlayBins[i]?.hits ?? 0),
			label: { x: lastX + 4, y: Math.max(PAD.top + 12, yOf(endTop) - 6), anchor: "end" }
		};
	});

	let tip = $state(null);
	let el = $state(null);
	function show(event, bin, i) {
		const box = el.getBoundingClientRect();
		const scale = box.width / WIDTH;
		const cx = xOf(i) + stepX / 2;
		if (!multi) {
			tip = { bin, cx, i, x: cx * scale, y: yOf(bin.hits) * scale, j: 0 };
			return;
		}
		// the line nearest the pointer, up or down: the card points at that
		// line's point for this week
		const py = (event.clientY - box.top) / scale;
		let j = 0;
		bin.each.forEach((v, k) => {
			if (Math.abs(yOf(v) - py) < Math.abs(yOf(bin.each[j]) - py)) j = k;
		});
		tip = { bin, cx, x: cx * scale, y: yOf(bin.each[j]) * scale, j };
	}
	const fmt = (s) =>
		parse(s).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
	const weekLabel = (b) => {
		const e = new Date(parse(b.start).getTime() + 6 * DAY);
		return `Week of ${fmt(b.start).replace(/, \d{4}$/, "")} – ${fmt(iso(e))}`;
	};
</script>

<div class="word-timeline" class:small bind:this={el}>
	<svg viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="Fox WNBA articles containing “{word}”, by {weekly ? 'week' : 'day'}" onpointerleave={() => (tip = null)}>
		{#each yTicks as t}
			<line class="grid" x1={PAD.left} x2={WIDTH - PAD.right} y1={yOf(t)} y2={yOf(t)} />
			{#if axis}<text class="axis" x={PAD.left - 6} y={yOf(t) + 4} text-anchor="end">{t}</text>{/if}
		{/each}
		{#each ticks as t}
			<line class="tick" x1={t.x} x2={t.x} y1={PAD.top + plotH} y2={PAD.top + plotH + (xaxis ? 5 : 3)} />
			{#if xaxis}<text class="axis" x={t.x} y={PAD.top + plotH + 20} text-anchor="start">{t.label}</text>{/if}
		{/each}
		<line class="baseline" x1={PAD.left} x2={WIDTH - PAD.right} y1={PAD.top + plotH} y2={PAD.top + plotH} />
		{#if axis && !small && !quiet}
			<text class="axis-title" x={PAD.left} y={PAD.top - 8} text-anchor="start"
				>{unit === "mentions" ? "Mentions of" : "Articles that mention"}
				{combined ? `any of the ${list.length} words` : multi ? "the term" : `“${entry.word}”`}, per {weekly ? "week" : "day"}{#if !multi}
					{" "}· {total.toLocaleString()} total{/if}</text
			>
		{/if}
		{#if stacked}
			<!-- a stack a week: each word a segment, in the lines' colours -->
			{#each bins as bin, i (bin.start)}
				{@const sum = bin.each.reduce((a, v) => a + v, 0)}
				{#if sum}
					{#each entries as e, j (e.word)}
						{@const below = bin.each.slice(0, j).reduce((a, v) => a + v, 0)}
						{#if bin.each[j]}
							<rect
								class="seg"
								x={xOf(i) + 0.5}
								y={yOf(below + bin.each[j])}
								width={Math.max(1, stepX - 1)}
								height={Math.max(0, yOf(below) - yOf(below + bin.each[j]) - (j ? 1 : 0))}
								style="fill:{e.color}"
							/>
						{/if}
					{/each}
				{/if}
			{/each}
			<!-- the legend, since a stack has no line to label -->
			{#each entries as e, j (e.word)}
				<text class="legend" x={PAD.left + 4 + j * 150} y={PAD.top + 12} style="fill:{e.color}"
					>■ {e.word} <tspan class="legend-n">{totals[j]} total {unit}</tspan></text
				>
			{/each}
		{:else if multi}
			{#each lines as l, j (l.word)}
				<path class="line" d={l.d} style="stroke:{l.color}" />
				{#if totals[j]}<text
					class="line-label"
					x={l.label.x}
					y={l.label.y}
					text-anchor={l.label.anchor}
					style="fill:{l.color}">{l.word}{#if !small} <tspan class="legend-n">{totals[j]} total {unit}</tspan>{/if}</text
				>{/if}
			{/each}
			{#if tip}
				<!-- the point the card is about -->
				<circle class="point" cx={tip.cx} cy={yOf(tip.bin.each[tip.j])} r="4.5" style="fill:{entries[tip.j].color}" />
			{/if}
		{/if}
		{#if areaPath}
			<path class="area" d={areaPath.fill} style="fill:{color}" />
			<path class="line" d={areaPath.line} style="stroke:{color}" />
			{#each notes as n (n.word)}
				{#if !n.side}
					<line class="note-tick" x1={n.x} x2={n.x} y1={n.y - 3} y2={n.ly + 3} style="stroke:{color}" />
				{/if}
				<text class="line-label" x={n.lx} y={n.ly} text-anchor={n.side ? "end" : "middle"} style="fill:{color}"
					>{n.word}</text
				>
			{/each}
			{#if tip}
				<circle class="point" cx={tip.cx} cy={yOf(tip.bin.hits)} r="4" style="fill:{color}" />
			{/if}
		{/if}
		{#if overlayPath}
			<path class="area overlay" class:stacked={stackOn} d={overlayPath.fill} style="fill:{overlayColor}" />
			<path class="line" d={overlayPath.line} style="stroke:{overlayColor}" />
			<text class="line-label" x={overlayPath.label.x} y={overlayPath.label.y} text-anchor={overlayPath.label.anchor} style="fill:{overlayColor}"
				>{overlayEntries[0].word}</text
			>
			{#if tip && overlayBins[tip.i] !== undefined}
				<circle class="point" cx={tip.cx} cy={yOf(overlayPath.topOf(tip.i))} r="4" style="fill:{overlayColor}" />
			{/if}
		{/if}
		{#each bins as bin, i (bin.start)}
			{#if !multi && !area}
				<rect
					class="bar"
					class:lit={tip?.bin === bin}
					x={xOf(i) + 0.5}
					y={yOf(bin.hits)}
					width={Math.max(1, stepX - 1)}
					height={PAD.top + plotH - yOf(bin.hits)}
				/>
			{/if}
			<!-- a wide, invisible target, so the thin bars are hoverable -->
			<rect
				class="hit"
				x={xOf(i)}
				y={PAD.top}
				width={stepX}
				height={plotH}
				onpointerenter={(e) => show(e, bin, i)}
				onpointermove={(e) => show(e, bin, i)}
				role="presentation"
			/>
		{/each}
		{#if markX !== null}
			<line class="mark" x1={markX} x2={markX} y1={PAD.top - 2} y2={PAD.top + plotH} />
			{#if !small && !quiet}
				{@const right = markX < WIDTH - PAD.right - 80}
				<text class="mark-label" x={right ? markX + 6 : markX - 6} y={PAD.top - 8} text-anchor={right ? "start" : "end"}
					>{String(markLabel).trim() || fmt(String(mark).trim())}</text
				>
			{/if}
		{/if}

	</svg>
	{#if tip}
		<div class="tip" style="left:{tip.x}px; top:{tip.y}px">
			<strong>{weekly ? weekLabel(tip.bin) : fmt(tip.bin.start)}</strong>
			{#if overlayBins && overlayBins[tip.i]}
				<span class="stat" style="color:{overlayColor}">{overlayEntries[0].word}: {overlayBins[tip.i].hits} {unit}</span>
			{/if}
			{#if multi}
				<span class="stat lead" style="color:{entries[tip.j].color}"
					><span class="dot" style="background:{entries[tip.j].color}"></span>{entries[tip.j].word}: {tip.bin.each[tip.j]}
					{unit === "mentions" ? `mentions across ${tip.bin.articles} ${tip.bin.articles === 1 ? "article" : "articles"}` : `of ${tip.bin.articles} ${tip.bin.articles === 1 ? "article" : "articles"}`}</span
				>
				{#each entries as e, j (e.word)}
					{#if j !== tip.j && tip.bin.each[j]}
						<span class="stat muted"><span class="dot" style="background:{e.color}"></span>{e.word}: {tip.bin.each[j]}</span>
					{/if}
				{/each}
			{:else}
				<span class="stat">{tip.bin.hits} {unit === "mentions" ? "mentions across" : "of"} {tip.bin.articles} {tip.bin.articles === 1 ? "article" : "articles"}</span>
				{#if tip.bin.example}<span class="example">{tip.bin.example}</span>{/if}
			{/if}
		</div>
	{/if}
</div>

<style>
	.word-timeline {
		position: relative;
		max-width: 920px;
		margin: 6px auto 4px;
	}
	svg {
		width: 100%;
		height: auto;
		display: block;
	}
	.bar {
		fill: var(--color-fox);
	}
	.bar.lit {
		fill: var(--color-ink);
	}
	.hit {
		fill: transparent;
	}
	.seg {
		pointer-events: none;
	}
	.area {
		opacity: 0.22;
		pointer-events: none;
	}
	.small .axis,
	.small .line-label,
	.small .axis-title,
	.small .mark-label,
	.small .total,
	.small .legend {
		font-size: 17px;
	}
	.small .legend-n {
		font-size: 14px;
	}
	.note-tick {
		stroke-width: 1;
		opacity: 0.6;
	}
	.line {
		fill: none;
		stroke-width: 2;
		stroke-linejoin: round;
	}
	.line-label,
	.legend {
		font-family: var(--font-chart);
		font-size: 14px;
		font-weight: 700;
		paint-order: stroke;
		stroke: var(--color-bg, var(--color-page-orange));
		stroke-width: 3px;
	}
	.legend-n {
		font-weight: 400;
		fill: rgba(42, 21, 3, 0.6);
	}
	.point {
		stroke: var(--color-paper);
		stroke-width: 2;
		pointer-events: none;
	}
	.tip .lead {
		font-weight: 700;
	}
	.tip .dot {
		display: inline-block;
		width: 8px;
		height: 8px;
		border-radius: 50%;
		margin-right: 6px;
	}
	.tip .muted {
		color: var(--tip-sub);
	}
	.grid {
		stroke: rgba(42, 21, 3, 0.1);
	}
	.baseline,
	.tick {
		stroke: rgba(42, 21, 3, 0.45);
		stroke-width: 1;
	}
	.axis {
		font-family: var(--font-chart);
		font-size: 13px;
		fill: rgba(42, 21, 3, 0.65);
	}
	.mark {
		stroke: var(--color-ink);
		stroke-width: 1.5;
		stroke-dasharray: 4 3;
	}
	.axis-title {
		font-family: var(--font-chart);
		font-size: 12.5px;
		fill: rgba(42, 21, 3, 0.65);
	}
	.mark-label,
	.total {
		font-family: var(--font-chart);
		font-size: 13px;
		font-weight: 700;
		fill: var(--color-ink);
	}
	.total {
		font-weight: 400;
		fill: rgba(42, 21, 3, 0.6);
	}
	.tip {
		position: absolute;
		transform: translate(-50%, calc(-100% - 12px));
		width: 280px;
		max-width: 80vw;
		background: var(--tip-bg);
		color: var(--tip-ink);
		border: 1px solid var(--tip-border);
		border-radius: var(--tip-radius);
		box-shadow: var(--tip-shadow);
		font: var(--tip-body);
		padding: var(--tip-pad);
		pointer-events: none;
		z-index: 6;
	}
	/* the shared tooltip (variables.css) */
	.tip strong {
		font: var(--tip-title);
		color: var(--tip-ink);
	}
	.tip strong,
	.tip .stat,
	.tip .example {
		display: block;
	}
	.tip .stat {
		color: var(--tip-ink);
		margin-top: 3px;
	}
	.tip .example {
		margin-top: 9px;
		padding: 1px 0 1px 9px;
		border-left: 3px solid var(--tip-rule);
		font: var(--tip-quote);
		color: var(--tip-ink);
	}
	.area.overlay {
		opacity: 0.38;
	}
	.area.overlay.stacked {
		opacity: 0.8;
	}
</style>
