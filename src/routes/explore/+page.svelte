<script>
	// A scratch page for looking at the triangles: /explore
	// Search words, keep them, set a floor on uses, switch between the chyrons
	// and the closed captions, light a topic, play the years, and read a few
	// whole clips for any kept word. Not part of the story.
	import TernaryStatic from "$components/TernaryStatic.svelte";
	import chyData from "$data/chyrons.json";
	import capData from "$data/captions.json";
	import capExamples from "$data/captions_examples.json";

	const SOURCES = { captions: capData, chyrons: chyData };
	let source = $state("captions");
	let data = $derived(SOURCES[source]);
	let terms = $derived(
		(data.ternary ?? []).toSorted((a, b) => b.total - a.total)
	);
	let biggest = $derived(Math.max(1, ...terms.map((t) => t.total)));

	// --- search ---------------------------------------------------------------
	const MAX_LIT = 12;
	let query = $state("");
	let q = $derived(query.trim().toLowerCase());
	let partial = $derived(q ? terms.filter((t) => t.term.includes(q)) : []);
	let exact = $derived(terms.find((t) => t.term === q) ?? null);
	let suggestions = $derived(partial.slice(0, 8));
	let cursor = $state(-1);
	let open = $state(false);
	let picked = $state([]);
	let lastKept = $state(null);
	const keep = (term) => {
		if (!term) return;
		if (!picked.includes(term)) picked = [...picked, term];
		lastKept = term;
		query = "";
		open = false;
	};
	const drop = (word) => {
		picked = picked.filter((w) => w !== word);
		if (lastKept === word) lastKept = null;
	};
	function onKey(e) {
		if (e.key === "ArrowDown") {
			cursor = Math.min(cursor + 1, suggestions.length - 1);
			e.preventDefault();
		} else if (e.key === "ArrowUp") {
			cursor = Math.max(cursor - 1, -1);
			e.preventDefault();
		} else if (e.key === "Enter") {
			keep(cursor >= 0 ? suggestions[cursor]?.term : (exact?.term ?? suggestions[0]?.term));
		} else if (e.key === "Escape") {
			open = false;
		}
	}
	// the floor on uses runs on a log scale
	let slider = $state(0);
	let minTotal = $derived(Math.round(Math.pow(biggest, slider / 100)));

	let topic = $state("");
	let timeline = $state(false);
	let focus = $derived(exact?.term ?? lastKept);
	let groups = $derived([
		[...picked, ...(exact ? [exact.term] : partial.slice(0, MAX_LIT).map((t) => t.term))]
	]);
	// the kept words' clips, newest first
	let shown = $derived(lastKept ? terms.find((t) => t.term === lastKept) : null);
	let shownClips = $derived(
		shown && source === "captions" ? capExamples[shown.term] : null
	);
	// a remount when the source changes: the triangle reads its data once
	$effect(() => {
		source;
		picked = [];
		lastKept = null;
		query = "";
	});
</script>

<svelte:head><title>explore · triangles</title></svelte:head>

<main class="explore">
	<aside class="panel">
		<h1>Triangle explorer</h1>
		<p class="lede">
			A scratch page. Words the three networks used about the WNBA, placed by
			who used them more.
		</p>

		<div class="row">
			<span class="label">Source</span>
			<div class="toggle" role="group">
				{#each Object.keys(SOURCES) as s (s)}
					<button class:on={source === s} onclick={() => (source = s)}>{s}</button>
				{/each}
			</div>
		</div>
		<p class="note">
			{source === "captions"
				? `${(data.clips ? Object.values(data.clips).reduce((a, b) => a + b, 0) : 0).toLocaleString()} caption clips, Sept 2017 – Oct 2024; a word counts once per clip.`
				: "Chyron banners, Sept 2017 – Aug 2026; every use counts."}
			{terms.length.toLocaleString()} words.
		</p>

		<label class="control">
			<span class="label">Find a word</span>
			<div class="search-box">
				<input
					type="search"
					placeholder="Type a word…"
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
								onpointerdown={(e) => (e.preventDefault(), keep(t.term))}
							>
								<span class="term">{t.term}</span>
								<span class="uses">{t.total.toLocaleString()}</span>
							</li>
						{/each}
					</ul>
				{/if}
			</div>
			<span class="note">
				{#if q && !partial.length}No word contains “{q}”.
				{:else if q && !exact}{partial.length} words contain “{q}”; the {Math.min(MAX_LIT, partial.length)} most used are lit. Enter keeps the first.
				{:else if exact}Enter keeps “{exact.term}”.
				{:else}Type to light matching words; Enter keeps one.{/if}
			</span>
		</label>

		{#if picked.length}
			<div class="chips">
				{#each picked as word (word)}
					<span class="chip" class:on={lastKept === word}>
						<button class="pick" onclick={() => (lastKept = word)}>{word}</button>
						<button class="x" onclick={() => drop(word)} aria-label="remove">×</button>
					</span>
				{/each}
			</div>
		{/if}

		<label class="control">
			<span class="label">Minimum uses: <b>{minTotal.toLocaleString()}</b></span>
			<input type="range" min="0" max="100" step="1" bind:value={slider} />
		</label>

		<div class="row">
			<span class="label">Topic</span>
			<div class="toggle" role="group">
				<button class:on={topic === ""} onclick={() => (topic = "")}>none</button>
				<button class:on={topic === "polrace"} onclick={() => (topic = "polrace")}>race & politics</button>
				<button class:on={topic === "lgbtq"} onclick={() => (topic = "lgbtq")}>LGBTQ+</button>
			</div>
		</div>
		<label class="row check">
			<input type="checkbox" bind:checked={timeline} />
			<span class="label">Timeline (play the years)</span>
		</label>

		{#if shown}
			<section class="clips">
				<h2>
					“{shown.term}” · {shown.total.toLocaleString()} uses ·
					{#each data.channels as ch, i}
						<span class="share ch{i}">{ch} {Math.round(shown.shares[i] * 100)}%</span>
					{/each}
				</h2>
				{#if shownClips}
					{#each data.channels as ch, i (ch)}
						{#if shownClips[ch]?.length}
							<h3 class="ch{i}">{ch} · {shown.counts[i].toLocaleString()} clips</h3>
							{#each shownClips[ch] as c}
								<p class="clip">
									<span class="meta">{c.d} · {c.show}</span>
									{c.t}
									<a href={c.u} target="_blank" rel="noreferrer">watch ↗</a>
								</p>
							{/each}
						{/if}
					{/each}
				{:else if shown.ex}
					<p class="clip"><span class="meta">{shown.ex_ch}</span> {shown.ex}</p>
				{/if}
			</section>
		{/if}
	</aside>

	<div class="chart">
		{#key source}
			<TernaryStatic
				{source}
				{groups}
				{focus}
				{minTotal}
				topic={topic || null}
				{timeline}
				enclose={false}
				big
			/>
		{/key}
	</div>
</main>

<style>
	.explore {
		display: grid;
		grid-template-columns: 380px 1fr;
		gap: 24px;
		max-width: 1400px;
		margin: 0 auto;
		padding: 18px 20px 40px;
		align-items: start;
	}
	@media (max-width: 900px) {
		.explore {
			grid-template-columns: 1fr;
		}
	}
	.panel {
		position: sticky;
		top: 12px;
		max-height: calc(100vh - 24px);
		overflow: auto;
		background: rgba(255, 253, 248, 0.6);
		border-radius: 8px;
		padding: 14px 16px 18px;
	}
	h1 {
		font-size: 20px;
		margin: 0 0 4px;
	}
	.lede {
		margin: 0 0 12px;
		font-size: 13.5px;
		line-height: 1.4;
		color: rgba(42, 21, 3, 0.75);
	}
	.row {
		display: flex;
		align-items: center;
		gap: 10px;
		margin: 8px 0;
		flex-wrap: wrap;
	}
	.row.check {
		cursor: pointer;
	}
	.label {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11px;
		font-weight: 800;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: rgba(42, 21, 3, 0.65);
	}
	.toggle {
		display: inline-flex;
		border: 1px solid rgba(42, 21, 3, 0.3);
		border-radius: 5px;
		overflow: hidden;
	}
	.toggle button {
		border: 0;
		background: transparent;
		color: var(--color-ink);
		font: inherit;
		font-size: 12.5px;
		font-weight: 600;
		padding: 5px 10px;
		cursor: pointer;
	}
	.toggle button.on {
		background: var(--color-ink);
		color: #fff;
	}
	.control {
		display: block;
		margin: 12px 0 6px;
	}
	.control .label {
		display: block;
		margin-bottom: 4px;
	}
	.search-box {
		position: relative;
	}
	.search-box input {
		width: 100%;
		box-sizing: border-box;
		font: inherit;
		font-size: 14px;
		padding: 7px 10px;
		border: 1px solid rgba(42, 21, 3, 0.3);
		border-radius: 5px;
		background: #fff;
	}
	.suggest {
		position: absolute;
		z-index: 5;
		left: 0;
		right: 0;
		margin: 2px 0 0;
		padding: 4px 0;
		list-style: none;
		background: #fff;
		border: 1px solid rgba(42, 21, 3, 0.2);
		border-radius: 5px;
		box-shadow: 0 6px 20px rgba(42, 21, 3, 0.15);
	}
	.suggest li {
		display: flex;
		justify-content: space-between;
		padding: 5px 10px;
		font-size: 13.5px;
		cursor: pointer;
	}
	.suggest li.on,
	.suggest li:hover {
		background: rgba(42, 21, 3, 0.07);
	}
	.suggest .uses {
		color: rgba(42, 21, 3, 0.5);
		font-variant-numeric: tabular-nums;
	}
	.note {
		display: block;
		font-size: 12px;
		line-height: 1.45;
		color: rgba(42, 21, 3, 0.6);
		margin: 4px 0 0;
	}
	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin: 8px 0 4px;
	}
	.chip {
		display: inline-flex;
		align-items: center;
		border: 1px solid #9061c2;
		border-radius: 999px;
		overflow: hidden;
		font-size: 13px;
	}
	.chip.on {
		background: #9061c2;
		color: #fff;
	}
	.chip button {
		border: 0;
		background: transparent;
		color: inherit;
		font: inherit;
		cursor: pointer;
		padding: 3px 4px 3px 10px;
	}
	.chip .x {
		padding: 3px 8px 3px 2px;
		opacity: 0.7;
	}
	input[type="range"] {
		width: 100%;
	}
	.clips {
		margin-top: 16px;
		border-top: 1px solid rgba(42, 21, 3, 0.2);
		padding-top: 10px;
	}
	.clips h2 {
		font-size: 14px;
		margin: 0 0 6px;
		line-height: 1.5;
	}
	.clips h3 {
		font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
		font-size: 11px;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		margin: 10px 0 4px;
	}
	.share {
		margin-right: 8px;
		font-weight: 700;
	}
	.ch0 {
		color: var(--color-fox);
	}
	.ch1 {
		color: var(--color-cnn);
	}
	.ch2 {
		color: var(--color-msnbc);
	}
	.clip {
		font-size: 12.5px;
		line-height: 1.45;
		margin: 0 0 8px;
		color: var(--color-ink);
	}
	.clip .meta {
		display: block;
		font-size: 11px;
		color: rgba(42, 21, 3, 0.55);
	}
	.clip a {
		margin-left: 4px;
		font-size: 11.5px;
		color: var(--color-fox);
		text-decoration: none;
	}
	.chart :global(.ternary-static) {
		max-width: 900px;
		margin: 0 auto;
	}
</style>
