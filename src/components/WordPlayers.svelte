<script>
	// Which players a word attaches to: search a word and see, for each
	// player, the share of her sentences that contain it, Fox News beside the
	// five sports outlets. In the Doc:
	//   {.WordPlayers}
	//   word: dirty
	//   {}
	import { base } from "$app/paths";
	import roster from "$data/people.json";
	let { word = "dirty" } = $props();

	let data = $state(null);
	let loading = false;
	async function load() {
		if (data || loading) return;
		loading = true;
		try {
			data = await (await fetch(`${base}/data/word_players.json`)).json();
		} finally {
			loading = false;
		}
	}
	$effect(() => {
		load();
	});

	const MIN_SENTENCES = 100;
	let query = $state("");
	let picked = $state(String(word).trim().toLowerCase());
	let open = $state(false);
	let cursor = $state(-1);
	let q = $derived(query.trim().toLowerCase());
	let suggestions = $derived.by(() => {
		if (!data || q.length < 2) return [];
		const all = Object.keys(data.words);
		const total = (w) => Object.values(data.words[w]).reduce((s, [a, b]) => s + a + b, 0);
		const starts = all.filter((w) => w.startsWith(q)).sort((a, b) => total(b) - total(a));
		const inside = all.filter((w) => !w.startsWith(q) && w.includes(q)).sort((a, b) => total(b) - total(a));
		return [...starts, ...inside].slice(0, 8);
	});
	const choose = (w) => { picked = w; query = ""; cursor = -1; open = false; };
	function onKey(e) {
		if (e.key === "ArrowDown") { cursor = Math.min(cursor + 1, suggestions.length - 1); e.preventDefault(); }
		else if (e.key === "ArrowUp") { cursor = Math.max(cursor - 1, -1); e.preventDefault(); }
		else if (e.key === "Enter") { const w = cursor >= 0 ? suggestions[cursor] : suggestions[0] ?? (data?.words[q] ? q : null); if (w) choose(w); e.preventDefault(); }
		else if (e.key === "Escape") { query = ""; cursor = -1; }
	}

	let entry = $derived(data?.words?.[picked] ?? null);
	// every player with enough sentences on both sides, her rate on each
	let rows = $derived.by(() => {
		if (!data) return [];
		return Object.entries(data.totals)
			.filter(([, [f, o]]) => f >= MIN_SENTENCES && o >= MIN_SENTENCES)
			.map(([name, [f, o]]) => {
				const [nf, no] = entry?.[name] ?? [0, 0];
				return { name, nf, no, f, o, rf: nf / f, ro: no / o };
			})
			.filter((r) => r.nf + r.no > 0)
			.sort((a, b) => b.rf - a.rf || b.ro - a.ro);
	});
	let peak = $derived(Math.max(1e-6, ...rows.flatMap((r) => [r.rf, r.ro])));
	const pct = (v) => `${(v * 100).toFixed(v < 0.0095 ? 2 : 1)}%`;
	const face = (name) => (roster[name]?.face ? `${base}/net/${roster[name].face}` : null);
	let hovered = $state(null);
</script>

<div class="word-players">
	<h4 class="hed">Which players get the word <span class="the-word">“{picked}”</span></h4>
	<div class="controls">
		<div class="search-box">
			<input type="search" placeholder="Search for a word…" bind:value={query} autocomplete="off" spellcheck="false"
				onfocus={() => { load(); open = true; }} onblur={() => (open = false)} oninput={() => ((open = true), (cursor = -1))} onkeydown={onKey} />
			{#if open && q && suggestions.length}
				<ul class="suggest" role="listbox">
					{#each suggestions as w, i (w)}
						<li role="option" aria-selected={i === cursor} class:on={i === cursor} onpointerdown={(e) => (e.preventDefault(), choose(w))}><span class="term">{w}</span></li>
					{/each}
				</ul>
			{/if}
		</div>
	</div>
	{#if !data}
		<p class="note">Loading the words…</p>
	{:else if !entry}
		<p class="note">“{picked}” isn't common enough to chart.</p>
	{:else}
		<div class="table">
			<div class="row head">
				<span></span>
				<span class="col fox">in Fox News</span>
				<span class="col others">in the sports outlets</span>
			</div>
			{#each rows as r (r.name)}
				<div class="row" class:dim={hovered && hovered !== r.name} onmouseenter={() => (hovered = r.name)} onmouseleave={() => (hovered = null)} role="presentation">
					<span class="who">
						{#if face(r.name)}<img src={face(r.name)} alt="" />{:else}<span class="blank"></span>{/if}
						<span class="name">{r.name}</span>
					</span>
					<span class="cell">
						<span class="track"><span class="bar fox" style="width:{(100 * r.rf) / peak}%"></span></span>
						<span class="value">{pct(r.rf)} <small>{r.nf} of {r.f.toLocaleString()}</small></span>
					</span>
					<span class="cell">
						<span class="track"><span class="bar others" style="width:{(100 * r.ro) / peak}%"></span></span>
						<span class="value">{pct(r.ro)} <small>{r.no} of {r.o.toLocaleString()}</small></span>
					</span>
				</div>
			{/each}
		</div>
		<p class="note">Bars are the share of each player's sentences that contain “{picked}”, in Fox's WNBA articles and in the five sports outlets', April 2023 on. Players with at least {MIN_SENTENCES} sentences on each side; sorted by Fox's rate.</p>
	{/if}
</div>

<style>
	.word-players { max-width: 920px; margin: 8px auto 12px; }
	.hed { text-align: center; font-size: 19px; margin: 0 0 10px; color: var(--color-ink); }
	.the-word { color: var(--color-fox); }
	.controls { display: flex; justify-content: center; margin-bottom: 12px; }
	.search-box { position: relative; width: min(260px, 70vw); }
	.search-box input { width: 100%; box-sizing: border-box; font: inherit; font-size: 14px; padding: 6px 9px; border: 1px solid rgba(42, 21, 3, 0.3); border-radius: 3px; background: #fff; color: var(--color-ink); }
	.search-box input:focus { outline: 2px solid var(--color-fox); outline-offset: 1px; }
	.suggest { position: absolute; left: 0; right: 0; top: calc(100% + 4px); margin: 0; padding: 0; list-style: none; background: #fff; border: 1px solid rgba(42, 21, 3, 0.2); border-radius: 3px; box-shadow: 0 6px 18px rgba(42, 21, 3, 0.18); z-index: 6; overflow: hidden; }
	.suggest li { padding: 6px 10px; font-size: 14px; font-weight: 700; cursor: pointer; }
	.suggest li + li { border-top: 1px solid rgba(42, 21, 3, 0.08); }
	.suggest li:hover, .suggest li.on { background: rgba(42, 21, 3, 0.07); }
	.table { display: flex; flex-direction: column; gap: 2px; }
	.row { display: grid; grid-template-columns: 190px 1fr 1fr; align-items: center; gap: 12px; height: 30px; transition: opacity 120ms ease; }
	.row.head { height: 22px; margin-bottom: 4px; }
	.row.dim { opacity: 0.35; }
	.col { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 11.5px; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; }
	.col.fox { color: #003366; }
	.col.others { color: #6b4bb0; }
	.who { display: flex; align-items: center; gap: 8px; min-width: 0; }
	.who img, .who .blank { width: 26px; height: 26px; border-radius: 50%; object-fit: cover; background: #d8cdb6; flex: 0 0 auto; border: 1.5px solid rgba(255, 253, 248, 0.9); }
	.name { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 13px; font-weight: 600; color: var(--color-ink); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
	.cell { display: grid; grid-template-columns: 1fr auto; align-items: center; gap: 8px; }
	.track { display: block; height: 14px; }
	.bar { display: block; height: 100%; border-radius: 2px; min-width: 2px; }
	.bar.fox { background: #003366; }
	.bar.others { background: #6b4bb0; }
	.value { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 11.5px; font-weight: 700; color: var(--color-ink); white-space: nowrap; min-width: 88px; }
	.value small { font-weight: 400; color: rgba(42, 21, 3, 0.55); }
	.note { font-size: 12.5px; color: rgba(42, 21, 3, 0.65); text-align: center; margin: 10px 0 0; }
	@media (max-width: 640px) {
		.row { grid-template-columns: 120px 1fr 1fr; gap: 6px; }
		.value small { display: none; }
		.value { min-width: 40px; }
	}
</style>
