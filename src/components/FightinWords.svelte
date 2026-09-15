<script>
	// Fightin' Words plot (Monroe, Colaresi & Quinn)
	import { scaleLinear, scaleLog, scaleSqrt } from "d3-scale";
	import WordBars from "$components/WordBars.svelte";
	import { base } from "$app/paths";
	import fw from "$data/fighting_words.json";
	const data = fw.grid;
	// story-word examples ship inline; the full 17k-word set loads on first hover
	const litExamples = fw.lit;

	const FOX = "var(--color-fox-navy)"; // Fox's chart colour, set once in variables.css
	const OTHER = "#6b4bb0"; // the other outlets' purple
	const SIGNIFICANT = 1.96;
	const SANS = '"Helvetica Neue", Helvetica, Arial, sans-serif';

	// crude greedy wrap: SVG text has no box to flow inside
	function wrap(sentence, perLine = 48, lines = 3) {
		const words = sentence.split(" ");
		const out = [];
		let line = "";
		for (const word of words) {
			if ((line + " " + word).trim().length > perLine) {
				out.push(line.trim());
				line = word;
			} else line += " " + word;
			if (out.length === lines) break;
		}
		if (out.length < lines && line.trim()) out.push(line.trim());
		return out
			.slice(0, lines)
			.map((l, i) =>
				i === lines - 1 && words.join(" ").length > perLine * lines
					? l + "…"
					: l
			);
	}

	// the logos drawn under "use this more ↓" for each comparison pool
	// the logos each comparison group stands for (the footnote), and the one
	// logo each outlet's pill shows
	const LOGOS = {
		"all outlets": [
			"espn.svg",
			"cbs-sports.svg",
			"usa-today.svg",
			"the-athletic.png",
			"jws.png"
		],
		ESPN: ["espn.svg"],
		"CBS Sports": ["cbs-sports.svg"],
		"USA Today": ["usa-today.svg"],
		"The Athletic": ["the-athletic.png"],
		"Just Women's Sports": ["jws.png"],
		"CBS + USA Today": ["cbs-sports.svg", "usa-today.svg"]
	};
	const PILL_LOGO = {
		ESPN: "espn.svg",
		"CBS Sports": "cbs-sports.svg",
		"USA Today": "usa-today.svg",
		"The Athletic": "the-athletic.png",
		"Just Women's Sports": "jws.png"
	};
	const LOGO_WIDTH = {
		"yahoo.svg": 44,
		"espn.svg": 42,
		"cbs-sports.svg": 44,
		"usa-today.svg": 56,
		"the-athletic.png": 13,
		"jws.png": 13,
		"fox-news": 22
	};

	// `source` ({points, topLabel, bottomLabel}) lets another dataset borrow the chart
	let {
		highlight = null,
		bare = false,
		controls = true,
		mode = null,
		source = null,
		// chart: "scatter" (the quadrant) or "bars" (mirrored top words)
		chart = "scatter",
		// labels, scale, caps: see WordBars
		labels = "on",
		scale = "linear",
		caps = false,
		scores = false,
		// ngrams: 2 — two-word phrases instead of words (whole articles only)
		ngrams = 1,
		// fill: stretch the bar rows down the viewport (the scrolly sets it)
		fill = false
	} = $props();
	// the explore step can flip this with the words/phrases pills
	let bigrams = $state(false);
	$effect(() => {
		bigrams = String(ngrams).trim() === "2";
	});

	// the outlet pills, as on the dot plot: "all", then one logo per outlet
	const ALL_OUTLETS = "all outlets";

	// the words lit on the chart: a step's list, plus whatever the explore
	// step's search box finds or keeps
	let HIGHLIGHT = $derived(
		new Set([
			...(highlight ?? []).map((w) => w.toLowerCase()),
			...searchLit
		])
	);
	let beating = $derived(HIGHLIGHT.size > 0);

	const ALL = "all coverage";
	let text = $state(mode ?? "headlines");
	let against = $state(data.outlets[0]);
	let player = $state(ALL);

	let bodyMode = $derived(
		text === "articles" &&
			player === ALL &&
			(data.articleWords ?? []).length > 0
	);
	let words = $derived(
		bodyMode
			? bigrams
				? (data.articleBigrams ?? [])
				: data.articleWords
			: player === ALL
				? data.words
				: (data.byPlayer?.[player] ?? [])
	);
	// over articles, "all outlets" is literally the same corpus as "Yahoo + ESPN" — dedupe
	let articleOutlets = $derived.by(() => {
		const seen = new Map();
		for (const name of data.articleOutlets ?? []) {
			const key = JSON.stringify(data.articleOutletN?.[name] ?? {});
			if (!seen.has(key) || name !== "all outlets") seen.set(key, name);
		}
		return [...seen.values()];
	});
	let outletsHere = $derived(
		bodyMode
			? articleOutlets
			: player === ALL
				? data.outlets
				: Object.keys(data.playerN?.[player] ?? {}).sort()
	);
	let sample = $derived(
		(bodyMode
			? data.articleOutletN?.[against]
			: player === ALL
				? data.outletN?.[against]
				: data.playerN?.[player]?.[against]) ?? null
	);
	let floor = $derived(player === ALL ? 5 : 3);

	// --- the explore step's search box (as on the ternary) -----------------
	// typing lights the words containing the text (an exact match on its
	// own); Enter or a click keeps a word as a chip
	const MAX_LIT = 30;
	let query = $state("");
	let picked = $state([]);
	let q = $derived(query.trim().toLowerCase());
	let vocabulary = $derived(
		[...points]
			.map((pt) => ({ term: pt.word.toLowerCase(), n: pt.n, z: pt.z }))
			.sort((a, b) => b.n - a.n)
	);
	let exact = $derived(q ? (vocabulary.find((t) => t.term === q) ?? null) : null);
	let partial = $derived(
		q && !exact ? vocabulary.filter((t) => t.term.includes(q)) : []
	);
	let suggestions = $derived.by(() => {
		if (!q) return [];
		const starts = vocabulary.filter((t) => t.term.startsWith(q));
		const inside = vocabulary.filter(
			(t) => !t.term.startsWith(q) && t.term.includes(q)
		);
		return [...starts, ...inside].slice(0, 8);
	});
	let searchLit = $derived([
		...picked,
		...(exact ? [exact.term] : partial.slice(0, MAX_LIT).map((t) => t.term))
	]);
	let open = $state(false);
	let cursor = $state(-1);
	const choose = (word) => {
		if (!picked.includes(word)) picked = [...picked, word];
		query = "";
		cursor = -1;
	};
	const unpick = (word) => (picked = picked.filter((w) => w !== word));
	function onKey(e) {
		if (e.key === "ArrowDown") {
			cursor = Math.min(cursor + 1, suggestions.length - 1);
			e.preventDefault();
		} else if (e.key === "ArrowUp") {
			cursor = Math.max(cursor - 1, -1);
			e.preventDefault();
		} else if (e.key === "Enter") {
			const word = cursor >= 0 ? suggestions[cursor]?.term : exact?.term;
			if (word) choose(word);
			e.preventDefault();
		} else if (e.key === "Escape") {
			query = "";
			cursor = -1;
		}
	}

	let points = $derived(
		source
			? source.points
			: words
					.filter(
						(entry) =>
							entry.z[against] !== undefined &&
							(entry.n?.[against] ?? 0) >= floor
					)
					.map((entry) => ({
						word: entry.word,
						z: entry.z[against],
						n: entry.n[against],
						nf: entry.nf?.[against] ?? 0,
						no: entry.no?.[against] ?? 0
					}))
	);

	$effect(() => {
		if (!outletsHere.includes(against)) against = outletsHere[0];
	});

	let viewportWidth = $state(
		typeof window === "undefined" ? 1200 : window.innerWidth
	);
	let mobile = $derived(viewportWidth < 640);
	let WIDTH = $derived(mobile ? 480 : 880);
	let HEIGHT = $derived(mobile ? 620 : 560);
	let PAD = $derived(
		mobile
			? { top: 26, right: 22, bottom: 52, left: 44 }
			: { top: 26, right: 40, bottom: 48, left: 52 }
	);

	// the domain must survive an empty or single-valued set
	let xScale = $derived(
		scaleLog()
			.domain([
				Math.max(3, Math.min(1e9, ...points.map((p) => p.n))),
				Math.max(30, ...points.map((p) => p.n))
			])
			.range([PAD.left, WIDTH - PAD.right])
	);
	let reach = $derived(Math.max(5, ...points.map((p) => Math.abs(p.z))));
	let yScale = $derived(
		scaleLinear()
			.domain([-reach, reach])
			.range([HEIGHT - PAD.bottom, PAD.top])
	);
	let sizeScale = $derived(scaleSqrt().domain([0, reach]).range([1.4, 6]));

	// real label widths, measured in the chart's own font once it is on the page
	let rootEl = $state(null);
	let measureCtx = null;
	function textWidth(word, size, weight) {
		if (typeof document === "undefined" || !rootEl)
			return word.length * size * 0.5;
		if (!measureCtx)
			measureCtx = document.createElement("canvas").getContext("2d");
		measureCtx.font = `${weight} ${size}px ${getComputedStyle(rootEl).fontFamily}`;
		return measureCtx.measureText(word).width;
	}

	let labelled = $derived.by(() => {
		rootEl; // re-run once the font can be measured
		// a player chart has few enough words to label them all: the weak ones
		// (near the middle: both sides use the word about equally) in a lighter
		// hand, so the strong ones still read first. The big archive chart
		// labels only what clears the threshold.
		const strong = source
			? points
			: points.filter((p) => Math.abs(p.z) > SIGNIFICANT);
		const isLit = (p) =>
			HIGHLIGHT.has(p.word.toLowerCase()) || HIGHLIGHT.has(p.word);
		const ranked = [
			...strong.filter(isLit).sort((a, b) => Math.abs(b.z) - Math.abs(a.z)),
			...strong
				.filter((p) => !isLit(p))
				.sort((a, b) => Math.abs(b.z) - Math.abs(a.z))
		];
		const placed = [];
		// the more words a step names, the smaller their labels: a dozen at
		// full size, forty at about two thirds
		const litSize = (full) =>
			Math.round(full * Math.max(0.68, 1 - Math.max(0, HIGHLIGHT.size - 12) * 0.011) * 2) / 2;
		// a label's box, for the clash test
		const boxFor = (point, px, py, side, size, weight, rowH) => {
			// plus the paint-order halo on each side
			const w = textWidth(point.word, size, weight) + 18;
			return {
				x0: side < 0 ? px - 6 - w : px + 6,
				x1: side < 0 ? px - 6 : px + 6 + w,
				y0: py - rowH / 2,
				y1: py + rowH / 2
			};
		};
		const clashes = (box) =>
			placed.some(
				(o) =>
					box.x0 < o.box.x1 &&
					o.box.x0 < box.x1 &&
					box.y0 < o.box.y1 &&
					o.box.y0 < box.y1
			);
		for (const point of ranked) {
			const lit = isLit(point);
			if (beating && !lit) continue;
			if (!source && placed.length > 34 && !lit) continue;
			// the archive chart: a word nobody named needs a real score to earn
			// a label, so a lone weak word at the edge does not get one just
			// because it has room
			if (!source && !lit && Math.abs(point.z) < 8) continue;
			const px = xScale(point.n),
				py = yScale(point.z);
			const weak = Boolean(source) && Math.abs(point.z) <= SIGNIFICANT;
			// the label's font, as the stylesheet sets it (.big for player charts)
			const size = source
				? weak
					? 17
					: lit
						? 28
						: 24
				: mobile
					? lit
						? litSize(18.5)
						: 15.5
					: lit
						? litSize(22)
						: 18;
			const weight = lit ? 800 : weak ? 500 : 600;
			const rowH = size * 1.3;
			// try beside the dot, then the other side, then a row up or down,
			// before giving up; a player chart tries harder, since every word
			// there gets a label
			const nearRight = px > WIDTH - PAD.right - 70;
			const sides = nearRight ? [-1, 1] : [1, -1];
			// a named word on the archive chart searches a long way for room:
			// the step's words must all show
			// a label may move a row or two to find room, no further: a word
			// that finds none is left unlabelled (its dot still lights)
			const shifts = source
				? [0, -0.8, 0.8, -1.6, 1.6, -2.4, 2.4, -3.2, 3.2]
				: [0, -0.8, 0.8, -1.6, 1.6];
			let spot = null;
			for (const dy of shifts) {
				for (const side of sides) {
					const box = boxFor(
						point,
						px,
						py + dy * rowH,
						side,
						size,
						weight,
						rowH
					);
					if (box.x0 < PAD.left || box.x1 > WIDTH - PAD.right + 4) continue;
					// never outside the drawing: a label pushed off the top or bottom is no label
					if (box.y0 < 2 || box.y1 > HEIGHT - PAD.bottom + 6) continue;
					if (!clashes(box)) {
						spot = { side, dy, box };
						break;
					}
				}
				if (spot) break;
			}
			if (!spot) continue;
			placed.push({
				...point,
				size,
				px,
				py: py + spot.dy * rowH,
				// where the dot is, and whether the label had to leave it
				dotY: py,
				moved: Math.abs(spot.dy) >= 1.6,
				lit,
				flip: spot.side < 0,
				weak,
				box: spot.box
			});
		}
		return placed;
	});

	let hovered = $state(null);
	let tip = $state(null);
	function showTip(event, point) {
		hovered = point.word;
		if (!source) ensureExamples();
		const box = event.currentTarget
			.closest(".fightin-words")
			?.getBoundingClientRect();
		tip = {
			...point,
			px: xScale(point.n),
			py: yScale(point.z),
			cx: box ? event.clientX - box.left : 0,
			cy: box ? event.clientY - box.top : 0,
			boxW: box ? box.width : 0,
			boxH: box ? box.height : 0
		};
	}
	const hideTip = () => {
		hovered = null;
		tip = null;
	};

	let fullExamples = $state(null);
	async function ensureExamples() {
		if (fullExamples) return;
		try {
			fullExamples = (await import("$data/fighting_words_examples.json"))
				.default;
		} catch {
			fullExamples = {};
		}
	}
	// against one outlet, that outlet's side quotes that outlet
	// (notebooks/06 → static/data/fw_examples_by_outlet.json), fetched once
	let outletExamples = $state(null);
	let outletExamplesLoading = false;
	async function ensureOutletExamples() {
		if (outletExamples || outletExamplesLoading) return;
		outletExamplesLoading = true;
		try {
			outletExamples = await (await fetch(`${base}/data/fw_examples_by_outlet.json`)).json();
		} catch {
			outletExamples = {};
		} finally {
			outletExamplesLoading = false;
		}
	}
	$effect(() => {
		if (against !== ALL_OUTLETS) ensureOutletExamples();
	});
	// the example for a word: the chosen outlet's own sentence when the word
	// sits on that outlet's side, else the shared one
	function exampleFor(mode, word, z) {
		if (against !== ALL_OUTLETS && z < 0) {
			const own = outletExamples?.[against]?.[mode]?.[word];
			if (own) return own;
		}
		return litExamples[mode]?.[word] ?? fullExamples?.[mode]?.[word];
	}

	// the bars take the same points, with short side names for their heads
	let barSource = $derived(
		source ?? {
			points,
			topShort: "in Fox News",
			bottomShort:
				against === ALL_OUTLETS ? "in the other outlets" : `in ${against}`
		}
	);
	// a bar's example on hover, from the same stores as the scatter's card
	function barExample(word, z = 0) {
		const mode = bodyMode ? (bigrams ? "bigrams" : "articles") : "headlines";
		const hit = exampleFor(mode, word, z);
		return hit?.[0] ? { s: hit[0], w: hit[1], o: hit[2] ?? null } : null;
	}

	let cardEx = $derived.by(() => {
		if (!tip) return null;
		if (source) return tip.eg ? { s: tip.eg, w: tip.egw, o: tip.ego ?? null } : null;
		const mode = bodyMode ? (bigrams ? "bigrams" : "articles") : "headlines";
		const hit = exampleFor(mode, tip.word, tip.z ?? 0);
		return { s: hit?.[0] ?? null, w: hit?.[1] ?? null, o: hit?.[2] ?? null };
	});

	// a beat swap can leave a stale tip captioned with the new side labels
	$effect(() => {
		source;
		hideTip();
	});

	const colorOf = (z) =>
		Math.abs(z) < SIGNIFICANT ? "rgba(42,21,3,0.28)" : z > 0 ? FOX : OTHER;

	const escapeHtml = (t) =>
		t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
	// the exact seen form wins ("held"); lemma prefix is the fallback ("hold" → "holding")
	const escRx = (t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
	const wordRx = (word, form) =>
		form
			? new RegExp("\\b" + escRx(form) + "\\b", "i")
			: new RegExp("\\b" + escRx(word) + "\\w*", "i");

	// window around the word; irregular inflections may not match — fall back to the opening
	function excerpt(sentence, word, form, budget = 300) {
		if (sentence.length <= budget) return sentence;
		const m =
			(form && wordRx(word, form).exec(sentence)) ||
			wordRx(word).exec(sentence);
		if (!m) return sentence.slice(0, budget).replace(/\s\S*$/, "") + "…";
		let start = Math.max(0, m.index - Math.round(budget * 0.45));
		if (start + budget > sentence.length)
			start = Math.max(0, sentence.length - budget);
		let out = sentence.slice(start, start + budget);
		if (start > 0) out = "…" + out.replace(/^\S*\s/, "");
		if (start + budget < sentence.length) out = out.replace(/\s\S*$/, "") + "…";
		return out;
	}

	function markWord(sentence, word, color, form) {
		const safe = escapeHtml(excerpt(sentence, word, form));
		const rx =
			form && wordRx(word, form).test(safe) ? wordRx(word, form) : wordRx(word);
		return safe.replace(
			rx,
			(m) =>
				`<mark style="background:${color}2e;box-shadow:inset 0 -2px 0 ${color}66;` +
				`color:inherit;padding:0 1px;">${m}</mark>`
		);
	}
	const tickValues = [10, 100, 1000, 10000];
</script>

<svelte:window bind:innerWidth={viewportWidth} />

<div
	class="fightin-words"
	class:bare
	class:mobile
	class:big={!!source}
	bind:this={rootEl}
>
	{#if !source}
		<div class="controls">
			<span class="label">Fox News compared with</span>
			<div class="picker" role="group" aria-label="Outlet">
				{#each outletsHere as outlet}
					{#if outlet === ALL_OUTLETS}
						<button
							class="all"
							class:active={against === outlet}
							onclick={() => (against = outlet)}>all</button
						>
					{:else if PILL_LOGO[outlet]}
						<button
							class:active={against === outlet}
							class:pooled={against === ALL_OUTLETS}
							class:square={PILL_LOGO[outlet].endsWith(".png")}
							title={outlet}
							aria-label={outlet}
							onclick={() => (against = outlet)}
						>
							<img src="{base}/logos/{PILL_LOGO[outlet]}" alt="" />
						</button>
					{:else}
						<button
							class="named"
							class:active={against === outlet}
							onclick={() => (against = outlet)}>{outlet}</button
						>
					{/if}
				{/each}
			</div>
		</div>
	{/if}
	{#if controls && !source}
		<!-- the explore step: find a word on the chart -->
		<div class="controls find">
			{#if bodyMode && (data.articleBigrams ?? []).length}
				<div class="picker ngram" role="group" aria-label="Words or phrases">
					<button class="named" class:active={!bigrams} onclick={() => (bigrams = false)}
						>words</button
					>
					<button class="named" class:active={bigrams} onclick={() => (bigrams = true)}
						>phrases</button
					>
				</div>
			{/if}
			<span class="label">Find a word</span>
			<div class="search-box">
				<input
					type="search"
					placeholder="Search for a word…"
					bind:value={query}
					autocomplete="off"
					spellcheck="false"
					onfocus={() => (open = true)}
					onblur={() => (open = false)}
					oninput={() => ((open = true), (cursor = -1))}
					onkeydown={onKey}
				/>
				{#if open && q && suggestions.length}
					<ul class="suggest" role="listbox">
						{#each suggestions as t, i (t.term)}
							<li
								role="option"
								aria-selected={i === cursor}
								class:on={i === cursor}
								onpointerdown={(e) => (e.preventDefault(), choose(t.term))}
							>
								<span class="term">{t.term}</span>
								<span class="uses" style="color:{t.z > 0 ? FOX : OTHER}"
									>{t.z > 0 ? "Fox" : "others"} · {t.n.toLocaleString()}</span
								>
							</li>
						{/each}
					</ul>
				{/if}
			</div>
			{#each picked as word (word)}
				<span class="kept">
					{word}
					<button
						type="button"
						aria-label="Remove {word}"
						onclick={() => unpick(word)}>×</button
					>
				</span>
			{/each}
		</div>
	{/if}

	{#if sample && !source}
		<p class="sample">
			{#if player === ALL}
				{sample.fox.toLocaleString()} Fox {bodyMode ? "articles" : "headlines"} against
				{sample.other.toLocaleString()} from {against}, April 2023 on.
			{:else}
				{sample.fox.toLocaleString()} Fox headlines name {player}, against
				{sample.other.toLocaleString()} from {against}.
			{/if}
			{#if Math.min(sample.fox, sample.other) < 400}
				Thin on one side — read this one as a sketch, not a finding.
			{/if}
		</p>
	{/if}

	{#if chart === "bars"}
		<!-- the same words as mirrored bars: the strongest on each side -->
		<WordBars
			{labels}
			{scale}
			{caps}
			{scores}
			source={barSource}
			{fill}
			otherName={against === ALL_OUTLETS ? "others" : against}
			highlight={[...HIGHLIGHT]}
			top={mobile ? 10 : 14}
			example={barExample}
			onhover={() => {
				if (!source) ensureExamples();
			}}
		/>
	{:else}
		<svg
			viewBox="0 0 {WIDTH} {HEIGHT}"
			role="img"
			aria-label="Weighted log-odds z-score against word frequency, Fox News versus {against}"
		>
			<!-- the band where a difference isn't distinguishable from chance -->
			<rect
				x={PAD.left}
				y={yScale(SIGNIFICANT)}
				width={WIDTH - PAD.right - PAD.left}
				height={yScale(-SIGNIFICANT) - yScale(SIGNIFICANT)}
				fill="rgba(42,21,3,0.05)"
			/>

			{#each tickValues as tick}
				{#if tick >= xScale.domain()[0] && tick <= xScale.domain()[1]}
					<line
						class="grid"
						x1={xScale(tick)}
						x2={xScale(tick)}
						y1={PAD.top}
						y2={HEIGHT - PAD.bottom}
					/>
					<text
						class="axis"
						x={xScale(tick)}
						y={HEIGHT - PAD.bottom + 16}
						text-anchor="middle"
					>
						{tick.toLocaleString()}
					</text>
				{/if}
			{/each}
			{#each yScale.ticks(7) as tick}
				<text
					class="axis"
					x={PAD.left - 8}
					y={yScale(tick) + 3.5}
					text-anchor="end">{tick}</text
				>
			{/each}

			<line
				class="axis-line"
				x1={PAD.left}
				x2={WIDTH - PAD.right}
				y1={yScale(0)}
				y2={yScale(0)}
			/>

			<text
				class="axis-name"
				x={(PAD.left + WIDTH - PAD.right) / 2}
				y={HEIGHT - 10}
				text-anchor="middle"
			>
				how often the word is used, both archives together →
			</text>
			<text
				class="axis-name"
				transform="rotate(-90)"
				x={-(HEIGHT / 2)}
				y="14"
				text-anchor="middle"
			>
				weighted log-odds z-score
			</text>
			{#if source}
				<text class="side" x={PAD.left + 6} y={PAD.top + 2} fill={FOX}>
					{source.topLabel} ↑
				</text>
				<text
					class="side"
					x={PAD.left + 6}
					y={HEIGHT - PAD.bottom - 8}
					fill={OTHER}
				>
					{source.bottomLabel} ↓
				</text>
			{:else}
				<g transform="translate({PAD.left + 6},{PAD.top + 2})">
					<image
						href="{base}/logos/fox-news.svg"
						width="20"
						height="20"
						y="-14"
					/>
					<text class="side" x="26" y="2" fill={FOX}>uses this more ↑</text>
				</g>
				<g transform="translate({PAD.left + 6},{HEIGHT - PAD.bottom - 20})">
					{#each LOGOS[against] ?? [] as logo, i}
						<image
							href="{base}/logos/{logo}"
							x={(LOGOS[against] ?? [])
								.slice(0, i)
								.reduce((sum, l) => sum + LOGO_WIDTH[l] + 8, 0)}
							y="0"
							width={LOGO_WIDTH[logo]}
							height="13"
						/>
					{/each}
					<text class="side" x="0" y="28" fill={OTHER}>use this more ↓</text>
				</g>
			{/if}

			{#each points as point (point.word)}
				<circle
					cx={xScale(point.n)}
					cy={yScale(point.z)}
					r={Math.abs(point.z) < SIGNIFICANT
						? 1.5
						: sizeScale(Math.abs(point.z))}
					fill={colorOf(point.z)}
					opacity={beating && !HIGHLIGHT.has(point.word.toLowerCase())
						? 0.16
						: hovered && hovered !== point.word
							? 0.25
							: 0.75}
					onpointerenter={(e) => showTip(e, point)}
					onpointerleave={hideTip}
					role="presentation"
				/>
				<!-- a generous invisible target, because a 2px dot is unhittable -->
				<circle
					cx={xScale(point.n)}
					cy={yScale(point.z)}
					r="7"
					fill="transparent"
					onpointerenter={(e) => showTip(e, point)}
					onpointerleave={hideTip}
					role="presentation"
				/>
			{/each}

			{#each labelled as point (point.word)}
				<text
					class="word"
					class:lit={point.lit}
					class:weak={point.weak}
					x={point.px + (point.flip ? -6 : 6)}
					y={point.py + 3.5}
					text-anchor={point.flip ? "end" : "start"}
					style:font-size="{point.size}px"
					fill={colorOf(point.z)}
					opacity={hovered && hovered !== point.word ? 0.3 : 1}
					onpointerenter={(e) => showTip(e, point)}
					onpointermove={(e) => showTip(e, point)}
					onpointerleave={hideTip}
					role="presentation"
				>
					{point.word}
				</text>
			{/each}
		</svg>

		{#if tip}
			{@const side = tip.z > 0 ? FOX : OTHER}
			<div
				class="tip-card"
				class:flip={tip.cx > tip.boxW - 350}
				style="left:{tip.cx}px; top:{Math.min(
					Math.max(70, tip.cy),
					(tip.boxH || 500) - 70
				)}px;
					border-left-color:{side}"
			>
				<span class="tip-head" style="color:{side}">{tip.word}</span>
				<!-- the split behind the dot: uses on each side, and the score -->
				<span class="tip-count"
					>Fox {tip.nf.toLocaleString()} · others {tip.no.toLocaleString()} · z {tip.z > 0 ? "+" : ""}{tip.z.toFixed(1)}</span
				>
				{#if cardEx?.s}
					<p>{@html markWord(cardEx.s, tip.word, side, cardEx.w)}</p>
					{#if cardEx.o}<span class="tip-source">{cardEx.o}</span>{/if}
				{/if}
			</div>
		{/if}
	{/if}

	<p class="note">
		Weighted log-odds ratio with an informative Dirichlet prior (Monroe,
		Colaresi &amp; Quinn 2008), using <a
			href="https://github.com/jmhessel/FightingWords"
			target="_blank"
			rel="noreferrer">Jack Hessel's implementation</a
		>, over headlines from April 2023 on. &ldquo;All outlets&rdquo; pools ESPN,
		CBS Sports, USA Today, Just Women's Sports and The Athletic, which together
		publish far more than Fox — so the horizontal axis, which counts both
		archives at once, is mostly theirs. Hover any word for the split. The shaded
		band is |z| &lt; 1.96, where the difference is not distinguishable from
		chance.
	</p>
</div>

<style>
	.fightin-words {
		max-width: 900px;
		margin: 0 auto;
		position: relative;
	}
	.tip-card {
		position: absolute;
		z-index: 8;
		pointer-events: none;
		width: 320px;
		transform: translate(14px, -50%);
		background: var(--color-paper);
		border: 1px solid rgba(42, 21, 3, 0.14);
		border-left: 3px solid var(--color-fox); /* recoloured inline per side */
		border-radius: 3px;
		padding: 10px 13px 11px;
		box-shadow: 0 5px 20px rgba(42, 21, 3, 0.16);
	}
	.tip-card.flip {
		transform: translate(calc(-100% - 14px), -50%);
	}
	.tip-source {
		display: block;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 10.5px;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: rgba(42, 21, 3, 0.5);
		margin-top: 4px;
	}
	.tip-count {
		display: block;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11px;
		color: rgba(42, 21, 3, 0.55);
		margin-top: 2px;
	}
	.tip-head {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 12px;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
	}
	.tip-count {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 10.5px;
		color: rgba(42, 21, 3, 0.45);
		margin-left: 6px;
	}
	.tip-weak {
		display: block;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 10.5px;
		color: rgba(42, 21, 3, 0.5);
		margin-top: 2px;
	}
	.tip-card p {
		margin: 6px 0 0;
		font-size: 13.5px;
		line-height: 1.5;
		color: var(--color-ink);
	}
	.fightin-words.bare .note,
	.fightin-words.bare .sample {
		display: none;
	}
	.fightin-words .controls[hidden] {
		display: none;
	}

	.controls {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 10px;
		flex-wrap: wrap;
		margin-bottom: 8px;
	}
	.label {
		font-size: 13px;
		color: var(--color-ink);
	}
	/* the outlet pills, styled as on the dot plot */
	.picker {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		flex-wrap: wrap;
	}
	.picker button {
		display: inline-flex;
		align-items: center;
		border: 1px solid rgba(42, 21, 3, 0.3);
		border-radius: 999px;
		background: rgba(255, 253, 248, 0.35);
		padding: 3px 8px;
		cursor: pointer;
		font: inherit;
		font-size: 12px;
		color: var(--color-ink);
		opacity: 0.6;
		transition:
			opacity 150ms ease,
			background 150ms ease;
	}
	.picker button:hover {
		opacity: 0.9;
	}
	.picker button.pooled {
		opacity: 0.85;
	}
	.picker button.active {
		opacity: 1;
		background: rgba(255, 253, 248, 0.95);
		border-color: var(--color-ink);
		font-weight: 800;
		box-shadow: 0 1px 4px rgba(42, 21, 3, 0.18);
	}
	.picker img {
		display: block;
		height: 12px;
		width: auto;
	}
	.picker button.square img {
		height: 15px;
	}
	.picker .all,
	.picker .named {
		padding: 3px 9px;
		font-size: 11px;
	}
	.toggle-group {
		display: inline-flex;
		border: 1px solid rgba(42, 21, 3, 0.3);
		border-radius: 4px;
		overflow: hidden;
	}
	.toggle-group button {
		border: 0;
		background: transparent;
		color: var(--color-ink);
		padding: 5px 11px;
		font-size: 12.5px;
		font-weight: 600;
		cursor: pointer;
	}
	.toggle-group button.active {
		background: var(--color-ink);
		color: #fff;
	}
	/* the search box, as on the ternary's explore step */
	.controls.find {
		gap: 8px;
	}
	.picker.ngram {
		margin-right: 10px;
	}
	.search-box {
		position: relative;
		width: min(260px, 60vw);
	}
	.search-box input[type="search"] {
		width: 100%;
		box-sizing: border-box;
		font: inherit;
		font-size: 14px;
		padding: 6px 9px;
		border: 1px solid rgba(42, 21, 3, 0.3);
		border-radius: 3px;
		background: #fff;
		color: var(--color-ink);
	}
	.search-box input[type="search"]:focus {
		outline: 2px solid var(--color-fox);
		outline-offset: 1px;
	}
	.suggest {
		position: absolute;
		left: 0;
		right: 0;
		top: calc(100% + 4px);
		margin: 0;
		padding: 0;
		list-style: none;
		background: #fff;
		border: 1px solid rgba(42, 21, 3, 0.2);
		border-radius: 3px;
		box-shadow: 0 6px 18px rgba(42, 21, 3, 0.18);
		z-index: 6;
		overflow: hidden;
		text-align: left;
	}
	.suggest li {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		padding: 6px 10px;
		font-size: 14px;
		cursor: pointer;
	}
	.suggest li + li {
		border-top: 1px solid rgba(42, 21, 3, 0.08);
	}
	.suggest li:hover,
	.suggest li.on {
		background: rgba(42, 21, 3, 0.07);
	}
	.suggest .term {
		font-weight: 700;
	}
	.suggest .uses {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11px;
	}
	/* a kept word */
	.kept {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 12px;
		font-weight: 700;
		color: var(--color-ink);
		background: rgba(255, 253, 248, 0.85);
		border: 1px solid rgba(42, 21, 3, 0.25);
		border-radius: 999px;
		padding: 2px 6px 2px 9px;
	}
	.kept button {
		border: 0;
		background: transparent;
		color: rgba(42, 21, 3, 0.6);
		font-size: 14px;
		line-height: 1;
		padding: 0 2px;
		cursor: pointer;
	}

	svg {
		width: 100%;
		height: auto;
		display: block;
	}
	.grid {
		stroke: rgba(42, 21, 3, 0.12);
		stroke-width: 1;
	}
	.axis-line {
		stroke: rgba(42, 21, 3, 0.45);
		stroke-width: 1;
	}
	.axis {
		font-size: 11.5px;
		fill: rgba(42, 21, 3, 0.6);
	}
	.axis-name {
		font-size: 12.5px;
		fill: rgba(42, 21, 3, 0.65);
	}
	.side {
		font-size: 13px;
		font-weight: 800;
	}
	.word {
		font-size: 18px;
		font-weight: 600;
		cursor: default;
		paint-order: stroke;
		stroke: var(--color-paper);
		stroke-width: 3px;
		stroke-linejoin: round;
	}
	.word.lit {
		font-size: 22px;
		font-weight: 800;
		stroke-width: 5.5px;
	}
	/* a word both sides use about equally: labelled, but in a lighter hand */
	.word.weak {
		font-size: 14px;
		font-weight: 500;
		opacity: 0.72;
	}
	.mobile .word.weak {
		font-size: 12.5px;
	}
	.big .word.weak {
		font-size: 17px;
	}

	.mobile .axis {
		font-size: 14px;
	}
	.mobile .axis-name {
		font-size: 14px;
	}
	.mobile .side {
		font-size: 15px;
	}
	.mobile .word {
		font-size: 15.5px;
	}
	.mobile .word.lit {
		font-size: 18.5px;
	}
	.mobile .tip-word {
		font-size: 18px;
	}

	/* declared after .mobile so it wins there */
	.big .word {
		font-size: 24px;
	}
	.big .word.lit {
		font-size: 28px;
		stroke-width: 6px;
	}
	.big .axis {
		font-size: 13px;
	}
	.big .axis-name {
		font-size: 13.5px;
	}
	.big .side {
		font-size: 17px;
	}
	.big .tip-word {
		font-size: 22px;
	}

	.tip {
		pointer-events: none;
	}
	.tip text {
		paint-order: stroke;
		stroke: var(--color-paper);
		stroke-width: 4px;
		stroke-linejoin: round;
	}
	.tip.carded text {
		paint-order: normal;
		stroke: none;
	}
	.tip-word {
		font-size: 15px;
		font-weight: 800;
	}
	.tip.carded .tip-word {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 12px;
		font-weight: 700;
		fill: #fff;
	}
	.tip-line {
		font-size: 11.5px;
		font-weight: 600;
		fill: rgba(42, 21, 3, 0.75);
	}

	.controls.dimmed {
		opacity: 0.4;
		pointer-events: none;
	}

	.sample {
		font-size: 12.5px;
		color: rgba(42, 21, 3, 0.72);
		text-align: center;
		max-width: 620px;
		margin: 2px auto 6px;
	}

	.note {
		font-size: 12px;
		line-height: 1.5;
		color: rgba(42, 21, 3, 0.62);
		text-align: center;
		max-width: 640px;
		margin: 12px auto 0;
	}
	.note a {
		color: inherit;
	}
</style>
