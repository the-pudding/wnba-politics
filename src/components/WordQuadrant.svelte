<script>
	// ---------------------------------------------------------------------------
	// Fightin' Words, drawn the way Monroe, Colaresi and Quinn draw it.
	//
	//   x  how often the word occurs at all, on a log scale
	//   y  the weighted log-odds z-score: above zero is Fox, below is the other
	//      outlet
	//
	// Reading it: common words sit far right, rare ones far left, and the ones
	// worth caring about are the ones that climb away from the middle. A word can
	// only be far from zero if the difference survives its own sample size, which
	// is what the Dirichlet prior buys — "trans" at z = 9 on a few hundred uses is
	// a real difference; a word used twice cannot get there.
	//
	// Points inside ±1.96 are drawn faint: that band is where the difference
	// isn't distinguishable from chance.
	//
	// Doc embed:  chart: word-quadrant
	// ---------------------------------------------------------------------------
	import { scaleLinear, scaleLog, scaleSqrt } from "d3-scale";
	import { base } from "$app/paths";
	import data from "$data/fighting_words_grid.json";
	// examples for the story's highlighted words ship with the page (7KB); the
	// full 17k-word set loads lazily on first hover
	import litExamples from "$data/fw_examples_lit.json";

	const FOX = "#c0392b";
	const OTHER = "#2a1503";
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

	// which logos stand for each side of the comparison
	const LOGOS = {
		"all outlets": ["yahoo", "espn", "cbs-sports", "usa-today"],
		"Yahoo + ESPN": ["yahoo", "espn"],
		"CBS + USA Today": ["cbs-sports", "usa-today"]
	};
	const LOGO_WIDTH = { yahoo: 44, espn: 42, "cbs-sports": 44, "usa-today": 56, "fox-news": 22 };

	// A scrollytelling wrapper passes its own words in, one beat at a time; with
	// nothing passed the chart falls back to the story's standing set.
	// `bare` drops the footnote and sample line — inside a scrolly they overflow
	// the sticky box and land on the prose below. `controls` is separate, so the
	// explore beat can hand back the pickers without bringing the footnote.
	// `source` lets another dataset borrow this chart wholesale: pass {points,
	// topLabel, bottomLabel, note} and the pickers, logos and internal corpus
	// selection step aside. Everything downstream — the dot sizing, the label
	// collision rule, the white-outlined highlights, the hover tag — is the same
	// code, which is the point: two Fightin' Words figures that disagree visually
	// look like two different claims.
	let { highlight = null, bare = false, controls = true, mode = null,
		source = null } = $props();

	const DEFAULT_HIGHLIGHT = new Set(["white", "foul", "fouls", "calls", "alleged", "trans",
		"transgender", "privilege", "womens", "media", "star", "fans", "social",
		"olympics", "Donald Trump", "Caitlin Clark"]);
	let HIGHLIGHT = $derived(
		highlight?.length ? new Set(highlight.map((w) => w.toLowerCase())) : DEFAULT_HIGHLIGHT
	);
	// during a beat, everything that isn't called out recedes
	let beating = $derived(Boolean(highlight?.length));

	const ALL = "all coverage";
	// Headlines are eight words of editing; the body is where the framing gets
	// argued. They don't always agree, so the two are read as separate charts.
	let text = $state(mode ?? "headlines");
	let against = $state(data.outlets[0]);
	// Restricting both corpora to the headlines that name one player is the
	// closest thing to holding the topic constant across archives — which is what
	// Monroe et al. do before comparing vocabularies at all.
	let player = $state(ALL);

	let bodyMode = $derived(text === "articles" && player === ALL && (data.articleWords ?? []).length > 0);
	let words = $derived(
		bodyMode ? data.articleWords
		: player === ALL ? data.words
		: (data.byPlayer?.[player] ?? [])
	);
	// an outlet only appears when both sides cleared the minimum
	// Only Yahoo and ESPN have full text, so over articles the "all outlets"
	// pooling is literally the same corpus as "Yahoo + ESPN". Showing both would
	// offer a choice that isn't one — keep the honest name.
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
	// per-player corpora are small, so a word needs fewer uses to be worth drawing
	let floor = $derived(player === ALL ? 5 : 3);

	let points = $derived(source ? source.points :
		words
			.filter((entry) => entry.z[against] !== undefined && (entry.n?.[against] ?? 0) >= floor)
			.map((entry) => ({
				word: entry.word, z: entry.z[against], n: entry.n[against],
				// counted per side, because the two archives are wildly different
				// sizes and a pooled number alone looks like an error
				nf: entry.nf?.[against] ?? 0, no: entry.no?.[against] ?? 0
			}))
	);

	$effect(() => {
		if (!outletsHere.includes(against)) against = outletsHere[0];
	});

	// Mobile draws fewer units in the same screen width (so type renders ~1.8x
	// larger) and taller; the right-hand ranked lists are dropped — at phone
	// width they would eat half the plot.
	let viewportWidth = $state(typeof window === "undefined" ? 1200 : window.innerWidth);
	let mobile = $derived(viewportWidth < 640);
	let WIDTH = $derived(mobile ? 480 : 880);
	let HEIGHT = $derived(mobile ? 620 : 560);
	let PAD = $derived(mobile
		? { top: 26, right: 22, bottom: 52, left: 44 }
		: { top: 26, right: 40, bottom: 48, left: 52 });

	// a thin player can leave almost nothing above the floor, so the domain needs
	// to survive an empty or single-valued set
	let xScale = $derived(scaleLog()
		.domain([Math.max(3, Math.min(1e9, ...points.map((p) => p.n))),
			Math.max(30, ...points.map((p) => p.n))])
		.range([PAD.left, WIDTH - PAD.right]));
	let reach = $derived(Math.max(5, ...points.map((p) => Math.abs(p.z))));
	let yScale = $derived(scaleLinear().domain([-reach, reach]).range([HEIGHT - PAD.bottom, PAD.top]));
	let sizeScale = $derived(scaleSqrt().domain([0, reach]).range([1.4, 6]));

	// Label the strongest words, skipping any that would land on top of one
	// already placed. Words we care about for the story jump the queue and are
	// allowed to collide — everything else yields.
	let labelled = $derived.by(() => {
		// A borrowed dataset is a few dozen words, so the labelling is generous —
		// but not unconditional. Labelling literally everything put "safe" (2 uses
		// against 3) on the plot dressed as a finding. A word earns its label by
		// clearing significance, or by being frequent enough (10+ uses) that its
		// NOT separating the two sides is itself worth seeing.
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
			// a borrowed (player) dataset is a few dozen words wearing big type,
			// so its collision boxes are roughly double
			const charW = source ? (mobile ? 7 : 8.5) : mobile ? 5.6 : 5.9;
			const rowH = source ? (mobile ? 24 : 27) : mobile ? 19 : 21;
			const clash = placed.some((other) =>
				Math.abs(other.px - px) < (other.word.length + point.word.length) * charW &&
				Math.abs(other.py - py) < rowH);
			if (clash) continue;
			// near the right edge a label would run into the ranked lists, so it
			// flips to the left of its dot instead
			const flip = px > WIDTH - PAD.right - 70;
			placed.push({ ...point, px, py, lit, flip });
		}
		return placed;
	});

	// hovering a dot pins its word, its z-score and how often it is used; without
	// it the cloud is 3,000 anonymous points
	let hovered = $state(null);
	let tip = $state(null);
	function showTip(event, point) {
		hovered = point.word;
		if (!source) ensureExamples();
		const box = event.currentTarget.closest(".word-quadrant")?.getBoundingClientRect();
		tip = { ...point, px: xScale(point.n), py: yScale(point.z),
			// client coords too: the example card is HTML, which wraps text
			// properly and can show a whole sentence instead of three hand-broken
			// lines ending in an ellipsis
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

	// what the hover card shows: the borrowed datasets carry their own example;
	// the main chart looks the word up — inline for the story words, then the
	// lazy full set. `s: null` still draws the card, just wordless-sentence-less,
	// so every hover speaks the same visual language.
	let cardEx = $derived.by(() => {
		if (!tip) return null;
		if (source) return tip.eg ? { s: tip.eg, w: tip.egw } : null;
		const mode = bodyMode ? "articles" : "headlines";
		const hit = litExamples[mode]?.[tip.word] ?? fullExamples?.[mode]?.[tip.word];
		return { s: hit?.[0] ?? null, w: hit?.[1] ?? null };
	});

	// A scrolly beat swaps the whole dataset under the cursor. A tip held from
	// the previous beat then renders the OLD word with the NEW side labels — a
	// Clark-vs-Reese count captioned "in Fox News · in the other outlets".
	$effect(() => {
		source;
		hideTip();
	});

	const colorOf = (z) => (Math.abs(z) < SIGNIFICANT ? "rgba(42,21,3,0.28)" : z > 0 ? FOX : OTHER);

	// The hovered word, marked inside its own example the same way the prose
	// marks ==words== — tinted wash plus underline — so the card reads as a
	// clipping from the story rather than a floating quote. Prefix match, because
	// the plot shows lemmas ("punch") and the sentence has inflections
	// ("punching").
	const escapeHtml = (t) =>
		t.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
	// The exact form seen at parse time wins ("held"); the lemma prefix is the
	// fallback for older data that only carries the lemma ("hold" → "holding").
	const escRx = (t) => t.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
	const wordRx = (word, form) => form
		? new RegExp("\\b" + escRx(form) + "\\b", "i")
		: new RegExp("\\b" + escRx(word) + "\\w*", "i");

	// A long example is windowed around the word rather than read from the top:
	// showing the first 300 characters of a passage whose point arrives at
	// character 350 is showing nothing. Cuts land on word boundaries, and a
	// missing match (irregular inflections — "send"/"sent") falls back to the
	// opening.
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

<div class="word-quadrant" class:bare class:mobile class:big={!!source}>
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
		<!-- the two poles, named by the outlets' own marks, or in words when
		     another dataset has borrowed the chart -->
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
			<!-- the label is a hover target too: it's bigger than its dot -->
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

		<!-- a word already carrying a label needs no tag repeating it; what it can
		     use is the sentence underneath -->
		<!-- the bare word tag, for the headline chart; the borrowed datasets get
		     an HTML card below instead, which can wrap a real sentence -->
	</svg>

	{#if tip && cardEx}
		{@const side = tip.z > 0 ? FOX : OTHER}
		<div class="tip-card" class:flip={tip.cx > tip.boxW - 350}
			style="left:{tip.cx}px; top:{Math.min(Math.max(70, tip.cy), (tip.boxH || 500) - 70)}px;
				border-left-color:{side}">
			<!-- just the word and its sentence — the stats live in the chart -->
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
		chance. ESPN, CBS and USA Today headlines come from URL slugs, so they lack punctuation and
		some short words.
	</p>
</div>

<style>
	.word-quadrant { max-width: 900px; margin: 0 auto; position: relative; }
	/* HTML rather than SVG so the sentence wraps by itself and arrives whole */
	.tip-card {
		position: absolute; z-index: 8; pointer-events: none;
		width: 320px; transform: translate(14px, -50%);
		background: #fffdf8; border: 1px solid rgba(42, 21, 3, 0.14);
		border-left: 3px solid #c0392b;   /* recoloured inline per side */
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
		margin: 6px 0 0; font-size: 13.5px; line-height: 1.5; color: #2a1503;
	}
	/* inside a scrolly the footnote overflows the sticky frame onto the prose */
	.word-quadrant.bare .note,
	.word-quadrant.bare .sample { display: none; }
	.word-quadrant .controls[hidden] { display: none; }

	.controls { display: flex; align-items: center; justify-content: center; gap: 10px; flex-wrap: wrap; margin-bottom: 8px; }
	.label { font-size: 13px; color: #2a1503; }
	.toggle-group { display: inline-flex; border: 1px solid rgba(42, 21, 3, 0.3); border-radius: 4px; overflow: hidden; }
	.toggle-group button {
		border: 0; background: transparent; color: #2a1503;
		padding: 5px 11px; font-size: 12.5px; font-weight: 600; cursor: pointer;
	}
	.toggle-group button.active { background: #2a1503; color: #fff; }

	svg { width: 100%; height: auto; display: block; }
	.grid { stroke: rgba(42, 21, 3, 0.12); stroke-width: 1; }
	.axis-line { stroke: rgba(42, 21, 3, 0.45); stroke-width: 1; }
	.axis { font-size: 11.5px; fill: rgba(42, 21, 3, 0.6); }
	.axis-name { font-size: 12.5px; fill: rgba(42, 21, 3, 0.65); }
	.side { font-size: 13px; font-weight: 800; }
	/* a white halo, so a label reads over the dot cloud rather than through it */
	.word {
		font-size: 18px; font-weight: 600; cursor: default;
		paint-order: stroke; stroke: #fffdf8; stroke-width: 3px;
		stroke-linejoin: round;
	}
	.word.lit { font-size: 22px; font-weight: 800; stroke-width: 5.5px; }

	/* mobile draws 480 units in the same width, so these render ~1.8x larger
	   again — the plot becomes the whole show */
	.mobile .axis { font-size: 14px; }
	.mobile .axis-name { font-size: 14px; }
	.mobile .side { font-size: 15px; }
	.mobile .word { font-size: 15.5px; }
	.mobile .word.lit { font-size: 18.5px; }
	.mobile .tip-word { font-size: 18px; }

	/* the player charts (borrowed datasets) hold a few dozen words, not 3,000 —
	   they can wear display-size type. Declared after .mobile so it wins there. */
	.big .word { font-size: 24px; }
	.big .word.lit { font-size: 28px; stroke-width: 6px; }
	.big .axis { font-size: 13px; }
	.big .axis-name { font-size: 13.5px; }
	.big .side { font-size: 17px; }
	.big .tip-word { font-size: 22px; }

	.tip { pointer-events: none; }
	/* the bare tag sits straight on the orange and needs an outline to survive;
	   on a card the same outline turns the text into a white-furred smear */
	.tip text { paint-order: stroke; stroke: #fffdf8; stroke-width: 4px; stroke-linejoin: round; }
	.tip.carded text { paint-order: normal; stroke: none; }
	.tip-word { font-size: 15px; font-weight: 800; }
	.tip.carded .tip-word {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 12px; font-weight: 700; fill: #fff;
	}
	.tip-line { font-size: 11.5px; font-weight: 600; fill: rgba(42, 21, 3, 0.75); }

	/* the player filter only exists for headlines; dim it rather than remove it,
	   so the control doesn't jump when the reader switches */
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
