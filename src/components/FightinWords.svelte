<script>
	// Fightin' Words plot (Monroe, Colaresi & Quinn): word frequency on a log x,
	// weighted log-odds z-score on y — Fox above zero, the other outlet below.
	// Doc embed:  chart: fightin-words
	import { scaleLinear, scaleLog, scaleSqrt } from "d3-scale";
	import { base } from "$app/paths";
	import fw from "$data/fighting_words.json";
	const data = fw.grid;
	// story-word examples ship inline; the full 17k-word set loads on first hover
	const litExamples = fw.lit;

	const FOX = "var(--color-fox)";
	const OTHER = "var(--color-ink)";
	const SIGNIFICANT = 1.96;
	const SANS = '"Helvetica Neue", Helvetica, Arial, sans-serif';

	// crude greedy wrap: SVG text has no box to flow inside
	function wrap(sentence, perLine = 48, lines = 3) {
		const words = sentence.split(" ");
		const out = [];
		let line = "";
		for (const word of words) {
			if ((line + " " + word).trim().length > perLine) { out.push(line.trim()); line = word; }
			else line += " " + word;
			if (out.length === lines) break;
		}
		if (out.length < lines && line.trim()) out.push(line.trim());
		return out.slice(0, lines).map((l, i) =>
			i === lines - 1 && words.join(" ").length > perLine * lines ? l + "…" : l);
	}

	const LOGOS = {
		"all outlets": ["yahoo", "espn", "cbs-sports", "usa-today"],
		"Yahoo + ESPN": ["yahoo", "espn"],
		"CBS + USA Today": ["cbs-sports", "usa-today"]
	};
	const LOGO_WIDTH = { yahoo: 44, espn: 42, "cbs-sports": 44, "usa-today": 56, "fox-news": 22 };

	// `source` ({points, topLabel, bottomLabel}) lets another dataset borrow the chart
	let { highlight = null, bare = false, controls = true, mode = null,
		source = null } = $props();

	let HIGHLIGHT = $derived(
		new Set((highlight ?? []).map((w) => w.toLowerCase()))
	);
	let beating = $derived(Boolean(highlight?.length));

	const ALL = "all coverage";
	let text = $state(mode ?? "headlines");
	let against = $state(data.outlets[0]);
	let player = $state(ALL);

	let bodyMode = $derived(text === "articles" && player === ALL && (data.articleWords ?? []).length > 0);
	let words = $derived(
		bodyMode ? data.articleWords
		: player === ALL ? data.words
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
		bodyMode ? articleOutlets
		: player === ALL ? data.outlets
		: Object.keys(data.playerN?.[player] ?? {}).sort()
	);
	let sample = $derived(
		(bodyMode ? data.articleOutletN?.[against]
			: player === ALL ? data.outletN?.[against]
			: data.playerN?.[player]?.[against]) ?? null
	);
	let floor = $derived(player === ALL ? 5 : 3);

	let points = $derived(source ? source.points :
		words
			.filter((entry) => entry.z[against] !== undefined && (entry.n?.[against] ?? 0) >= floor)
			.map((entry) => ({
				word: entry.word, z: entry.z[against], n: entry.n[against],
				nf: entry.nf?.[against] ?? 0, no: entry.no?.[against] ?? 0
			}))
	);

	$effect(() => {
		if (!outletsHere.includes(against)) against = outletsHere[0];
	});

	let viewportWidth = $state(typeof window === "undefined" ? 1200 : window.innerWidth);
	let mobile = $derived(viewportWidth < 640);
	let WIDTH = $derived(mobile ? 480 : 880);
	let HEIGHT = $derived(mobile ? 620 : 560);
	let PAD = $derived(mobile
		? { top: 26, right: 22, bottom: 52, left: 44 }
		: { top: 26, right: 40, bottom: 48, left: 52 });

	// the domain must survive an empty or single-valued set
	let xScale = $derived(scaleLog()
		.domain([Math.max(3, Math.min(1e9, ...points.map((p) => p.n))),
			Math.max(30, ...points.map((p) => p.n))])
		.range([PAD.left, WIDTH - PAD.right]));
	let reach = $derived(Math.max(5, ...points.map((p) => Math.abs(p.z))));
	let yScale = $derived(scaleLinear().domain([-reach, reach]).range([HEIGHT - PAD.bottom, PAD.top]));
	let sizeScale = $derived(scaleSqrt().domain([0, reach]).range([1.4, 6]));

	let labelled = $derived.by(() => {
		// n >= 10: frequent enough that not separating the sides is itself worth seeing
		const strong = source
			? points.filter((p) => Math.abs(p.z) > SIGNIFICANT || p.n >= 10)
			: points.filter((p) => Math.abs(p.z) > SIGNIFICANT);
		const isLit = (p) => HIGHLIGHT.has(p.word.toLowerCase()) || HIGHLIGHT.has(p.word);
		const ranked = [
			...strong.filter(isLit).sort((a, b) => Math.abs(b.z) - Math.abs(a.z)),
			...strong.filter((p) => !isLit(p)).sort((a, b) => Math.abs(b.z) - Math.abs(a.z))
		];
		const placed = [];
		for (const point of ranked) {
			const lit = isLit(point);
			if (beating && !lit) continue;
			if (!source && placed.length > 34 && !lit) continue;
			const px = xScale(point.n), py = yScale(point.z);
			const charW = source ? (mobile ? 7 : 8.5) : mobile ? 5.6 : 5.9;
			const rowH = source ? (mobile ? 24 : 27) : mobile ? 19 : 21;
			const clash = placed.some((other) =>
				Math.abs(other.px - px) < (other.word.length + point.word.length) * charW &&
				Math.abs(other.py - py) < rowH);
			if (clash) continue;
			const flip = px > WIDTH - PAD.right - 70;
			placed.push({ ...point, px, py, lit, flip });
		}
		return placed;
	});

	let hovered = $state(null);
	let tip = $state(null);
	function showTip(event, point) {
		hovered = point.word;
		if (!source) ensureExamples();
		const box = event.currentTarget.closest(".fightin-words")?.getBoundingClientRect();
		tip = { ...point, px: xScale(point.n), py: yScale(point.z),
			cx: box ? event.clientX - box.left : 0,
			cy: box ? event.clientY - box.top : 0,
			boxW: box ? box.width : 0,
			boxH: box ? box.height : 0 };
	}
	const hideTip = () => { hovered = null; tip = null; };

	let fullExamples = $state(null);
	async function ensureExamples() {
		if (fullExamples) return;
		try {
			fullExamples = (await import("$data/fighting_words_examples.json")).default;
		} catch { fullExamples = {}; }
	}

	let cardEx = $derived.by(() => {
		if (!tip) return null;
		if (source) return tip.eg ? { s: tip.eg, w: tip.egw } : null;
		const mode = bodyMode ? "articles" : "headlines";
		const hit = litExamples[mode]?.[tip.word] ?? fullExamples?.[mode]?.[tip.word];
		return { s: hit?.[0] ?? null, w: hit?.[1] ?? null };
	});

	// a beat swap can leave a stale tip captioned with the new side labels
	$effect(() => {
		source;
		hideTip();
	});

	const colorOf = (z) => (Math.abs(z) < SIGNIFICANT ? "rgba(42,21,3,0.28)" : z > 0 ? FOX : OTHER);

	const escapeHtml = (t) =>
		t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
	// the exact seen form wins ("held"); lemma prefix is the fallback ("hold" → "holding")
	const escRx = (t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
	const wordRx = (word, form) => form
		? new RegExp("\\b" + escRx(form) + "\\b", "i")
		: new RegExp("\\b" + escRx(word) + "\\w*", "i");

	// window around the word; irregular inflections may not match — fall back to the opening
	function excerpt(sentence, word, form, budget = 300) {
		if (sentence.length <= budget) return sentence;
		const m = (form && wordRx(word, form).exec(sentence)) || wordRx(word).exec(sentence);
		if (!m) return sentence.slice(0, budget).replace(/\s\S*$/, "") + "…";
		let start = Math.max(0, m.index - Math.round(budget * 0.45));
		if (start + budget > sentence.length) start = Math.max(0, sentence.length - budget);
		let out = sentence.slice(start, start + budget);
		if (start > 0) out = "…" + out.replace(/^\S*\s/, "");
		if (start + budget < sentence.length) out = out.replace(/\s\S*$/, "") + "…";
		return out;
	}

	function markWord(sentence, word, color, form) {
		const safe = escapeHtml(excerpt(sentence, word, form));
		const rx = form && wordRx(word, form).test(safe) ? wordRx(word, form) : wordRx(word);
		return safe.replace(rx, (m) =>
			`<mark style="background:${color}2e;box-shadow:inset 0 -2px 0 ${color}66;` +
			`color:inherit;padding:0 1px;">${m}</mark>`);
	}
	const tickValues = [10, 100, 1000, 10000];
</script>

<svelte:window bind:innerWidth={viewportWidth} />

<div class="fightin-words" class:bare class:mobile class:big={!!source}>
	{#if !source}
	<div class="controls">
		<span class="label">Fox News compared with</span>
		<div class="toggle-group" role="group" aria-label="Outlet">
			{#each outletsHere as outlet}
				<button class:active={against === outlet} onclick={() => (against = outlet)}>{outlet}</button>
			{/each}
		</div>
	</div>
	{/if}
	{#if controls && (data.articleWords ?? []).length && !source}
		<div class="controls">
			<span class="label">measured over</span>
			<div class="toggle-group" role="group" aria-label="Headlines or full text">
				<button class:active={text === "headlines"} onclick={() => (text = "headlines")}>headlines</button>
				<button class:active={text === "articles"} onclick={() => { text = "articles"; player = ALL; }}>
					whole articles
				</button>
			</div>
		</div>
	{/if}

	<div class="controls" class:dimmed={bodyMode} hidden={!controls || !!source}>
		<span class="label">in headlines about</span>
		<div class="toggle-group" role="group" aria-label="Player">
			<button class:active={player === ALL} onclick={() => (player = ALL)}>everyone</button>
			{#each data.players ?? [] as name}
				<button class:active={player === name} onclick={() => (player = name)}>{name}</button>
			{/each}
		</div>
	</div>

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

	<svg viewBox="0 0 {WIDTH} {HEIGHT}" role="img"
		aria-label="Weighted log-odds z-score against word frequency, Fox News versus {against}">
		<!-- the band where a difference isn't distinguishable from chance -->
		<rect x={PAD.left} y={yScale(SIGNIFICANT)} width={WIDTH - PAD.right - PAD.left}
			height={yScale(-SIGNIFICANT) - yScale(SIGNIFICANT)} fill="rgba(42,21,3,0.05)" />

		{#each tickValues as tick}
			{#if tick >= xScale.domain()[0] && tick <= xScale.domain()[1]}
				<line class="grid" x1={xScale(tick)} x2={xScale(tick)} y1={PAD.top} y2={HEIGHT - PAD.bottom} />
				<text class="axis" x={xScale(tick)} y={HEIGHT - PAD.bottom + 16} text-anchor="middle">
					{tick.toLocaleString()}
				</text>
			{/if}
		{/each}
		{#each yScale.ticks(7) as tick}
			<text class="axis" x={PAD.left - 8} y={yScale(tick) + 3.5} text-anchor="end">{tick}</text>
		{/each}

		<line class="axis-line" x1={PAD.left} x2={WIDTH - PAD.right} y1={yScale(0)} y2={yScale(0)} />

		<text class="axis-name" x={(PAD.left + WIDTH - PAD.right) / 2} y={HEIGHT - 10}
			text-anchor="middle">
			how often the word is used, both archives together →
		</text>
		<text class="axis-name" transform="rotate(-90)" x={-(HEIGHT / 2)} y="14" text-anchor="middle">
			weighted log-odds z-score
		</text>
		{#if source}
			<text class="side" x={PAD.left + 6} y={PAD.top + 2} fill={FOX}>
				{source.topLabel} ↑
			</text>
			<text class="side" x={PAD.left + 6} y={HEIGHT - PAD.bottom - 8} fill={OTHER}>
				{source.bottomLabel} ↓
			</text>
		{:else}
			<g transform="translate({PAD.left + 6},{PAD.top + 2})">
				<image href="{base}/logos/fox-news.svg" width="20" height="20" y="-14" />
				<text class="side" x="26" y="2" fill={FOX}>uses this more ↑</text>
			</g>
			<g transform="translate({PAD.left + 6},{HEIGHT - PAD.bottom - 20})">
				{#each LOGOS[against] ?? [] as logo, i}
					<image href="{base}/logos/{logo}.svg"
						x={(LOGOS[against] ?? []).slice(0, i).reduce((sum, l) => sum + LOGO_WIDTH[l] + 8, 0)}
						y="0" width={LOGO_WIDTH[logo]} height="13" />
				{/each}
				<text class="side" x="0" y="28" fill={OTHER}>use this more ↓</text>
			</g>
		{/if}

		{#each points as point (point.word)}
			<circle cx={xScale(point.n)} cy={yScale(point.z)}
				r={Math.abs(point.z) < SIGNIFICANT ? 1.5 : sizeScale(Math.abs(point.z))}
				fill={colorOf(point.z)}
				opacity={beating && !HIGHLIGHT.has(point.word.toLowerCase()) ? 0.16
					: hovered && hovered !== point.word ? 0.25 : 0.75}
				onpointerenter={(e) => showTip(e, point)}
				onpointerleave={hideTip}
				role="presentation" />
			<!-- a generous invisible target, because a 2px dot is unhittable -->
			<circle cx={xScale(point.n)} cy={yScale(point.z)} r="7" fill="transparent"
				onpointerenter={(e) => showTip(e, point)}
				onpointerleave={hideTip}
				role="presentation" />
		{/each}

		{#each labelled as point (point.word)}
			<text class="word" class:lit={point.lit}
				x={point.px + (point.flip ? -6 : 6)} y={point.py + 3.5}
				text-anchor={point.flip ? "end" : "start"}
				fill={colorOf(point.z)} opacity={hovered && hovered !== point.word ? 0.3 : 1}
				onpointerenter={(e) => showTip(e, point)}
				onpointermove={(e) => showTip(e, point)}
				onpointerleave={hideTip}
				role="presentation">
				{point.word}
			</text>
		{/each}

	</svg>

	{#if tip && cardEx}
		{@const side = tip.z > 0 ? FOX : OTHER}
		<div class="tip-card" class:flip={tip.cx > tip.boxW - 350}
			style="left:{tip.cx}px; top:{Math.min(Math.max(70, tip.cy), (tip.boxH || 500) - 70)}px;
				border-left-color:{side}">
			<span class="tip-head" style="color:{side}">{tip.word}</span>
			{#if cardEx.s}
				<p>{@html markWord(cardEx.s, tip.word, side, cardEx.w)}</p>
			{/if}
		</div>
	{/if}

	<p class="note">
		Weighted log-odds ratio with an informative Dirichlet prior (Monroe, Colaresi &amp; Quinn 2008),
		using <a href="https://github.com/jmhessel/FightingWords" target="_blank" rel="noreferrer">Jack
		Hessel's implementation</a>, over headlines from April 2023 on. &ldquo;All outlets&rdquo; pools
		Yahoo Sports, ESPN, CBS Sports and USA Today, which together publish far more than Fox — so the
		horizontal axis, which counts both archives at once, is mostly theirs. Hover any word for the
		split. The shaded band is |z| &lt; 1.96, where the difference is not distinguishable from
		chance.
	</p>
</div>

<style>
	.fightin-words { max-width: 900px; margin: 0 auto; position: relative; }
	.tip-card {
		position: absolute; z-index: 8; pointer-events: none;
		width: 320px; transform: translate(14px, -50%);
		background: var(--color-paper); border: 1px solid rgba(42, 21, 3, 0.14);
		border-left: 3px solid var(--color-fox);   /* recoloured inline per side */
		border-radius: 3px; padding: 10px 13px 11px;
		box-shadow: 0 5px 20px rgba(42, 21, 3, 0.16);
	}
	.tip-card.flip { transform: translate(calc(-100% - 14px), -50%); }
	.tip-head {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 12px; font-weight: 700; letter-spacing: 0.04em;
		text-transform: uppercase;
	}
	.tip-count {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 10.5px; color: rgba(42, 21, 3, 0.45); margin-left: 6px;
	}
	.tip-weak {
		display: block;
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 10.5px; color: rgba(42, 21, 3, 0.5); margin-top: 2px;
	}
	.tip-card p {
		margin: 6px 0 0; font-size: 13.5px; line-height: 1.5; color: var(--color-ink);
	}
	.fightin-words.bare .note,
	.fightin-words.bare .sample { display: none; }
	.fightin-words .controls[hidden] { display: none; }

	.controls { display: flex; align-items: center; justify-content: center; gap: 10px; flex-wrap: wrap; margin-bottom: 8px; }
	.label { font-size: 13px; color: var(--color-ink); }
	.toggle-group { display: inline-flex; border: 1px solid rgba(42, 21, 3, 0.3); border-radius: 4px; overflow: hidden; }
	.toggle-group button {
		border: 0; background: transparent; color: var(--color-ink);
		padding: 5px 11px; font-size: 12.5px; font-weight: 600; cursor: pointer;
	}
	.toggle-group button.active { background: var(--color-ink); color: #fff; }

	svg { width: 100%; height: auto; display: block; }
	.grid { stroke: rgba(42, 21, 3, 0.12); stroke-width: 1; }
	.axis-line { stroke: rgba(42, 21, 3, 0.45); stroke-width: 1; }
	.axis { font-size: 11.5px; fill: rgba(42, 21, 3, 0.6); }
	.axis-name { font-size: 12.5px; fill: rgba(42, 21, 3, 0.65); }
	.side { font-size: 13px; font-weight: 800; }
	.word {
		font-size: 18px; font-weight: 600; cursor: default;
		paint-order: stroke; stroke: var(--color-paper); stroke-width: 3px;
		stroke-linejoin: round;
	}
	.word.lit { font-size: 22px; font-weight: 800; stroke-width: 5.5px; }

	.mobile .axis { font-size: 14px; }
	.mobile .axis-name { font-size: 14px; }
	.mobile .side { font-size: 15px; }
	.mobile .word { font-size: 15.5px; }
	.mobile .word.lit { font-size: 18.5px; }
	.mobile .tip-word { font-size: 18px; }

	/* declared after .mobile so it wins there */
	.big .word { font-size: 24px; }
	.big .word.lit { font-size: 28px; stroke-width: 6px; }
	.big .axis { font-size: 13px; }
	.big .axis-name { font-size: 13.5px; }
	.big .side { font-size: 17px; }
	.big .tip-word { font-size: 22px; }

	.tip { pointer-events: none; }
	.tip text { paint-order: stroke; stroke: var(--color-paper); stroke-width: 4px; stroke-linejoin: round; }
	.tip.carded text { paint-order: normal; stroke: none; }
	.tip-word { font-size: 15px; font-weight: 800; }
	.tip.carded .tip-word {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 12px; font-weight: 700; fill: #fff;
	}
	.tip-line { font-size: 11.5px; font-weight: 600; fill: rgba(42, 21, 3, 0.75); }

	.controls.dimmed { opacity: 0.4; pointer-events: none; }

	.sample {
		font-size: 12.5px; color: rgba(42, 21, 3, 0.72); text-align: center;
		max-width: 620px; margin: 2px auto 6px;
	}

	.note {
		font-size: 12px; line-height: 1.5; color: rgba(42, 21, 3, 0.62);
		text-align: center; max-width: 640px; margin: 12px auto 0;
	}
	.note a { color: inherit; }
</style>
