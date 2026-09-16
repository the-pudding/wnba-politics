<script>
	// Words most associated with a word

	import { base } from "$app/paths";
	
	let { word = "foul", note = undefined, example = true, top = 16 } = $props();
	const noteMode = $derived(note === undefined || note === null ? "stock" : String(note).trim() ? "custom" : "none");
	const showExample = $derived(!(example === false || String(example).trim().toLowerCase() === "false"));
	const noteFor = (w, fox, others) =>
		String(note)
			.replace(/\{word\}/g, w)
			.replace(/\{fox\}/g, fox.toLocaleString())
			.replace(/\{others\}/g, others.toLocaleString());

	let data = $state(null);
	let loading = false;
	async function load() {
		if (data || loading) return;
		loading = true;
		try {
			data = await (await fetch(`${base}/data/word_neighbors.json`)).json();
		} finally {
			loading = false;
		}
	}
	$effect(() => {
		load();
	});

	let measure = $state("weighted");
	let query = $state("");
	let picked = $state(String(word).trim().toLowerCase().replace(/ /g, "_").replace(/'/g, ""));
	let open = $state(false);
	let cursor = $state(-1);
	const show = (t) => data?.show?.[t] ?? t.replace(/_/g, " ");
	let q = $derived(query.trim().toLowerCase());
	let suggestions = $derived.by(() => {
		if (!data || q.length < 2) return [];
		const all = Object.keys(data.words);
		const starts = all.filter((w) => w.startsWith(q) || show(w).toLowerCase().startsWith(q));
		const inside = all.filter((w) => !starts.includes(w) && (w.includes(q) || show(w).toLowerCase().includes(q)));
		const n = (w) => (data.words[w].fox.n ?? 0) + (data.words[w].others.n ?? 0);
		return [...starts.sort((a, b) => n(b) - n(a)), ...inside.sort((a, b) => n(b) - n(a))].slice(0, 8);
	});
	const choose = (w) => {
		picked = w;
		query = "";
		cursor = -1;
		open = false;
	};
	function onKey(e) {
		if (e.key === "ArrowDown") { cursor = Math.min(cursor + 1, suggestions.length - 1); e.preventDefault(); }
		else if (e.key === "ArrowUp") { cursor = Math.max(cursor - 1, -1); e.preventDefault(); }
		else if (e.key === "Enter") {
			const w = cursor >= 0 ? suggestions[cursor] : suggestions[0] ?? (data?.words[q] ? q : null);
			if (w) choose(w);
			e.preventDefault();
		} else if (e.key === "Escape") { query = ""; cursor = -1; }
	}

	let TOP = $derived(Math.max(1, parseInt(String(top), 10) || 16));
	let entry = $derived(data?.words?.[picked] ?? null);
	// each column's list, ranked by the chosen measure
	const ranked = (side) =>
		[...(side?.near ?? [])]
			.map(([w, n, wt]) => ({ w, n, wt, v: measure === "raw" ? n : wt }))
			.filter((d) => d.v > 0)
			.sort((a, b) => b.v - a.v)
			.slice(0, TOP);
	let columns = $derived([
		// the other outlets on the left, Fox on the right, as on the bar charts
		{ key: "others", label: "other outlets", color: "var(--color-outlets)", rows: ranked(entry?.others), n: entry?.others?.n ?? 0 },
		{ key: "fox", label: "Fox News", color: "var(--color-fox-navy)", rows: ranked(entry?.fox), n: entry?.fox?.n ?? 0 }
	]);
	// each column on its own scale: the lists are rankings within a corpus,
	// and the lift's absolute size depends on how big the corpus is
	const peakOf = (col) => Math.max(1e-9, ...col.rows.map((d) => d.v));
	const fmt = (d) => (measure === "raw" ? d.n.toLocaleString() : `${d.wt.toFixed(d.wt < 10 ? 1 : 0)}×`);
	let hovered = $state(null);
</script>

<div class="word-neighbors">
	<h4 class="hed">Words most associated with <span class="the-word">“{show(picked)}”</span></h4>
	<div class="controls">
		<div class="toggle-group" role="group" aria-label="Measure">
			<button class:active={measure === "weighted"} onclick={() => (measure = "weighted")}>weighted</button>
			<button class:active={measure === "raw"} onclick={() => (measure = "raw")}>raw count</button>
		</div>
		<div class="search-box">
			<input
				type="search"
				placeholder="Search for a word…"
				bind:value={query}
				autocomplete="off"
				spellcheck="false"
				onfocus={() => { load(); open = true; }}
				onblur={() => (open = false)}
				oninput={() => ((open = true), (cursor = -1))}
				onkeydown={onKey}
			/>
			{#if open && q && suggestions.length}
				<ul class="suggest" role="listbox">
					{#each suggestions as w, i (w)}
						<li role="option" aria-selected={i === cursor} class:on={i === cursor} onpointerdown={(e) => (e.preventDefault(), choose(w))}>
							<span class="term">{show(w)}</span>
							<span class="uses">Fox {data.words[w].fox.n.toLocaleString()} · others {data.words[w].others.n.toLocaleString()}</span>
						</li>
					{/each}
				</ul>
			{/if}
		</div>
	</div>

	{#if !data}
		<p class="note">Loading the words…</p>
	{:else if !entry}
		<p class="note">“{show(picked)}” isn't common enough to chart (a word needs 40 uses).</p>
	{:else}
		<div class="columns">
			{#each columns as col (col.key)}
				<div class="column">
					<h5 style="color:{col.color}">{col.label}</h5>
					<div class="rows">
						{#each col.rows as d, i (d.w)}
							<div class="row" class:dim={hovered && hovered !== d.w} onmouseenter={() => (hovered = d.w)} onmouseleave={() => (hovered = null)} role="presentation">
								<span class="label">{show(d.w)}</span>
								<span class="track"><span class="bar" style="width:{(100 * d.v) / peakOf(col)}%; background:{col.color}; opacity:{0.55 + 0.45 * (1 - i / TOP)}"></span></span>
								<!-- the lift multiplier is not a number a reader can use; the bar
								     carries the ranking, and raw mode still prints its counts -->
								{#if measure === "raw"}<span class="value">{fmt(d)}</span>{/if}
							</div>
						{:else}
							<p class="note">Too rare here.</p>
						{/each}
					</div>
				</div>
			{/each}
		</div>
		<p class="note">
			{#if noteMode === "custom"}
				{@html noteFor(show(picked), entry.fox.n, entry.others.n)}
			{:else if noteMode === "stock"}
				{#if measure === "weighted"}
					Weighted: how many times more often a word sits right before or after “{show(picked)}” than its overall frequency would predict, among pairs seen at least four times.
				{:else}
					Raw: how many times a word sits right before or after “{show(picked)}”.
				{/if}
				“{show(picked)}” appears {entry.fox.n.toLocaleString()} times in Fox's WNBA articles and {entry.others.n.toLocaleString()} in the five sports outlets', April 2023 on.
			{/if}
			{#if showExample && entry.fox.eg}<span class="eg">{entry.fox.eg}</span>{/if}
		</p>
	{/if}
</div>

<style>
	.word-neighbors { max-width: 920px; margin: 8px auto 12px; position: relative; }
	.hed { text-align: center; font-size: 19px; margin: 0 0 10px; color: var(--color-ink); }
	.the-word { color: var(--color-fox); }
	.controls { display: flex; align-items: center; justify-content: center; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }
	.toggle-group { display: inline-flex; border: 1px solid rgba(42, 21, 3, 0.3); border-radius: 4px; overflow: hidden; }
	.toggle-group button { border: 0; background: transparent; color: var(--color-ink); padding: 5px 11px; font-size: 12.5px; font-weight: 600; cursor: pointer; }
	.toggle-group button.active { background: var(--color-ink); color: #fff; }
	.search-box { position: relative; width: min(240px, 60vw); }
	.search-box input { width: 100%; box-sizing: border-box; font: inherit; font-size: 14px; padding: 6px 9px; border: 1px solid rgba(42, 21, 3, 0.3); border-radius: 3px; background: #fff; color: var(--color-ink); }
	.search-box input:focus { outline: 2px solid var(--color-fox); outline-offset: 1px; }
	.suggest { position: absolute; left: 0; right: 0; top: calc(100% + 4px); margin: 0; padding: 0; list-style: none; background: #fff; border: 1px solid rgba(42, 21, 3, 0.2); border-radius: 3px; box-shadow: 0 6px 18px rgba(42, 21, 3, 0.18); z-index: 6; overflow: hidden; text-align: left; }
	.suggest li { display: flex; justify-content: space-between; align-items: baseline; gap: 8px; padding: 6px 10px; font-size: 14px; cursor: pointer; }
	.suggest li + li { border-top: 1px solid rgba(42, 21, 3, 0.08); }
	.suggest li:hover, .suggest li.on { background: rgba(42, 21, 3, 0.07); }
	.suggest .term { font-weight: 700; }
	.suggest .uses { font-family: var(--font-chart); font-size: 11px; color: rgba(42, 21, 3, 0.55); white-space: nowrap; }
	/* the two columns, as on the chyron chart: word, bar, value */
	.columns { display: grid; grid-template-columns: 1fr 1fr; gap: 10px 36px; }
	.column h5 { margin: 0 0 8px; font-family: var(--font-chart); font-size: 13px; font-weight: 800; letter-spacing: 0.04em; text-transform: uppercase; text-align: center; }
	.row { display: grid; grid-template-columns: minmax(80px, 42%) 1fr auto; align-items: center; gap: 8px; height: 24px; transition: opacity 120ms ease; }
	.row.dim { opacity: 0.35; }
	.label { font-family: var(--font-chart); font-size: 13px; font-weight: 600; color: var(--color-ink); text-align: right; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.track { display: block; height: 14px; }
	.bar { display: block; height: 100%; border-radius: 2px; min-width: 2px; }
	.value { font-family: var(--font-chart); font-size: 11px; color: rgba(42, 21, 3, 0.6); min-width: 34px; }
	.note { font-size: 12.5px; color: rgba(42, 21, 3, 0.65); text-align: center; margin: 10px 0 0; }
	.note .eg { display: block; font-style: italic; color: var(--color-ink); margin-top: 4px; }
	@media (max-width: 640px) {
		.columns { grid-template-columns: 1fr; gap: 18px; }
	}
</style>
