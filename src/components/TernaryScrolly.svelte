<script>
	// Chyron ternary walked through
	import { base } from "$app/paths";
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import TernaryStatic from "$components/TernaryStatic.svelte";
	import chy from "$data/chyrons.json";
	import { faces, clipPops } from "$utils/clips.js";
	import { fade, fly } from "svelte/transition";
	import { cubicOut } from "svelte/easing";

	// note: the line under the triangle (see TernaryStatic); {period} is filled in
	let { steps = null, note = null } = $props();

	// ArchieML gives "viktor, bout / merchant, death" — one group per slash
	const parseGroups = (step) => {
		const raw = (step.groups ?? step.words ?? "").trim();
		if (!raw) return [];
		return raw
			.split(/\/+/) // "a, b / c, d" or "a, b // c, d" — either separator
			.map((band) =>
				band
					.split(",")
					.map((w) => w.trim())
					.filter(Boolean)
			)
			.filter((band) => band.length);
	};
	const STEPS = $derived(
		(steps ?? [])
			// a step counts if it has anything to show: text, a title, words, or the search
			.filter(
				(step) =>
					(step.text ?? "").trim() ||
					(step.title ?? "").trim() ||
					parseGroups(step).length ||
					step.search
			)
			.map((step) => ({
				title: (step.title ?? "").trim(),
				groups: parseGroups(step),
				img: (step.img ?? "").trim(),
				search: step.search === true || step.search === "true",
				html: step.text ?? ""
			}))
	);

	let index = $state(0);
	let last = $state(0);
	$effect(() => {
		if (index !== undefined && index !== null) last = index;
	});
	let current = $derived(STEPS[last] ?? STEPS[0]);

	// --- the explore step -------------------------------------------------
	const MIN_TOTAL = 1;
	const vocabulary = (chy.ternary ?? [])
		.filter((t) => t.total >= MIN_TOTAL)
		.map((t) => ({ term: t.term, total: t.total }))
		.sort((a, b) => b.total - a.total);
	const biggest = vocabulary[0]?.total ?? 100;
	const MAX_LIT = 30;
	let query = $state("");
	let q = $derived(query.trim().toLowerCase());
	// an exact match is pinned as you type; without one, words containing the
	// text are lit as a hint. Enter keeps the exact match as a chip.
	let exact = $derived(
		q ? (vocabulary.find((t) => t.term === q) ?? null) : null
	);
	let partial = $derived(
		q && !exact ? vocabulary.filter((t) => t.term.includes(q)) : []
	);
	// suggestions for the box: words starting with the text first, then
	// containing it, most-used first
	let suggestions = $derived.by(() => {
		if (!q) return [];
		const starts = vocabulary.filter((t) => t.term.startsWith(q));
		const inside = vocabulary.filter(
			(t) => !t.term.startsWith(q) && t.term.includes(q)
		);
		return [...starts, ...inside].slice(0, 8);
	});
	// the dropdown: open while the box has focus and text; arrow keys move, Enter
	// takes the highlighted word (or the exact match), a click takes that word
	let open = $state(false);
	let cursor = $state(-1);
	const choose = (word) => {
		if (!picked.includes(word)) picked = [...picked, word];
		lastKept = word;
		query = "";
		cursor = -1;
	};
	function onKey(e) {
		if (e.key === "ArrowDown") {
			cursor = Math.min(cursor + 1, suggestions.length - 1);
			e.preventDefault();
		} else if (e.key === "ArrowUp") {
			cursor = Math.max(cursor - 1, -1);
			e.preventDefault();
		} else if (e.key === "Enter") {
			if (cursor >= 0 && suggestions[cursor]) choose(suggestions[cursor].term);
			else keep();
		} else if (e.key === "Escape") {
			open = false;
		}
	}
	let picked = $state([]);
	// the word most recently kept stays pinned until something else happens
	let lastKept = $state(null);
	const keep = () => {
		if (!exact) return;
		if (!picked.includes(exact.term)) picked = [...picked, exact.term];
		lastKept = exact.term;
		query = "";
	};
	const drop = (word) => {
		picked = picked.filter((w) => w !== word);
		// nothing stays pinned after a removal
		lastKept = null;
		focus = null;
	};
	// the slider runs on a log scale: a single use at the left, the most-used word at the right
	let slider = $state(0);
	let minTotal = $derived(
		Math.round(MIN_TOTAL * Math.pow(biggest / MIN_TOTAL, slider / 100))
	);

	// the chip being hovered (or tapped) pins its tooltip on the triangle; on the
	// explore step the exact match being typed, else the last word kept, is pinned
	let focus = $state(null);
	// clicking away from the chips and the panel unpins whatever was pinned
	function unpin(event) {
		if (event.target.closest?.(".chip, .panel")) return;
		focus = null;
		lastKept = null;
	}
	let pinned = $derived(
		focus ?? (current.search ? (exact?.term ?? lastKept) : null)
	);
	let groups = $derived(
		current.search
			? [
					[
						...picked,
						...(exact
							? [exact.term]
							: partial.slice(0, MAX_LIT).map((t) => t.term))
					]
				]
			: current.groups
	);
</script>

<svelte:window onclick={unpin} />

<section class="ternary-scrolly" class:explore={current.search}>
	<div class="sticky">
		<TernaryStatic
			{groups}
			{note}
			bare
			big
			highlightColor="var(--color-fox-navy)"
			enclose={!current.search}
			focus={pinned}
			minTotal={current.search ? minTotal : 0}
		/>

		{#if current.search}
			<!-- the explore step's controls stay put: beside the triangle on wide
			     screens, under it on phones, so they never sit over the points -->
			<aside class="panel">
				<!-- the panel eases in like a card arriving, rather than popping -->
				<div
					class="panel-inner"
					in:fly|global={{ y: 16, duration: 480, easing: cubicOut }}
					out:fade|global={{ duration: 180 }}
				>
				{#if current.title}<h4 class="card-title">{current.title}</h4>{/if}
				{#if current.html}<p class="card-text">
						{@html clipPops(faces(current.html, base), base)}
					</p>{/if}
				<label class="control">
					<span class="control-label"
						>Minimum uses: <b>{minTotal.toLocaleString()}</b></span
					>
					<input type="range" min="0" max="100" step="1" bind:value={slider} />
					<span class="ends" aria-hidden="true">
						<span>1</span><span>{biggest.toLocaleString()}</span>
					</span>
				</label>
				<label class="control">
					<span class="control-label">Find a word</span>
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
										<span class="uses">{t.total.toLocaleString()}</span>
									</li>
								{/each}
							</ul>
						{/if}
					</div>
					{#if q && !exact}
						<span class="control-note">
							{#if !partial.length}
								No word contains “{q}”.
							{:else if partial.length > MAX_LIT}
								{partial.length} words contain “{q}”; the {MAX_LIT} most common are
								lit.
							{:else}
								{partial.length}
								{partial.length === 1 ? "word contains" : "words contain"} “{q}”.
							{/if}
						</span>
					{:else if exact}
						<span class="control-note">Press Enter to keep “{exact.term}”.</span
						>
					{/if}
				</label>
				{#if picked.length}
					<div class="chips">
						{#each picked as word (word)}
							<span
								class="chip"
								class:on={pinned === word}
								role="button"
								tabindex="0"
								onpointerenter={() => (focus = word)}
								onpointerleave={() => (focus = null)}
							>
								{word}
								<button
									class="x"
									aria-label="remove {word}"
									onclick={() => drop(word)}>×</button
								>
							</span>
						{/each}
					</div>
				{/if}
			</div>
			</aside>
		{/if}
	</div>

	<div class="steps">
		<Scrolly bind:value={index}>
			{#each STEPS as step, i}
				<div class="step" class:active={last === i}>
					{#if !step.search}
						<div class="card">
							{#if step.title}<h4 class="card-title">{step.title}</h4>{/if}
							{#if step.html}<p class="card-text">
									{@html clipPops(faces(step.html, base), base)}
								</p>{/if}
							{#each step.groups as group}
								<div class="chips">
									{#each group as word}
										<button
											class="chip"
											class:on={focus === word}
											onpointerenter={() => (focus = word)}
											onpointerleave={() => (focus = null)}
											onclick={() => (focus = focus === word ? null : word)}
										>
											{word}
										</button>
									{/each}
								</div>
							{/each}
						</div>
						{#if step.img}
							<!-- the step's image scrolls with the card: centred over the
							     chart on wide screens, directly under the card on phones -->
							<img
								class="figure"
								src="{base}/images/{step.img}"
								alt=""
								loading="lazy"
							/>
						{/if}
					{/if}
				</div>
			{/each}
		</Scrolly>
		<!-- room after the last step, so the reader can scroll the final card
		     clear of the triangle while the explore state holds -->
		<div class="linger"></div>
	</div>
</section>

<style>
	.ternary-scrolly {
		position: relative;
		margin: 24px 0;
	}

	.sticky {
		position: sticky;
		top: 0;
		height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	.sticky :global(.ternary-static) {
		width: min(660px, 92vw);
	}
	.sticky :global(svg) {
		max-height: 82vh;
	}
	.figure {
		position: absolute;
		left: 50%;
		top: 50%;
		transform: translate(-50%, -50%);
		width: min(560px, 84vw);
		max-height: 70vh;
		object-fit: contain;
		background: var(--color-paper);
		border: 1px solid rgba(42, 21, 3, 0.2);
		border-radius: 4px;
		box-shadow: 0 8px 30px rgba(42, 21, 3, 0.22);
		opacity: 0.3;
		transition: opacity 250ms ease;
	}
	.step.active .figure {
		opacity: 1;
	}

	/* the explore panel: a card that stays put, at the left like the cards */
	.panel {
		position: absolute;
		left: 0;
		top: 50%;
		transform: translateY(-50%);
		width: 300px;
		box-sizing: border-box;
		background: rgba(255, 253, 248, 0.96);
		border-left: 3px solid var(--color-fox);
		padding: 14px 16px 15px;
		border-radius: 3px;
		font-size: 15.5px;
		line-height: 1.5;
		color: var(--color-ink);
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
		z-index: 2;
	}

	.steps {
		position: relative;
		z-index: 1;
		margin-top: -100vh;
		pointer-events: none;
	}
	.step {
		position: relative;
		height: 100vh;
		display: flex;
		align-items: center;
		justify-content: flex-start;
		pointer-events: none;
	}
	.card {
		max-width: 300px;
		margin: 0;
		background: rgba(255, 253, 248, 0.94);
		border-left: 3px solid var(--color-fox);
		padding: 14px 16px 15px;
		border-radius: 3px;
		font-size: 15.5px;
		line-height: 1.5;
		color: var(--color-ink);
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
		opacity: 0.3;
		transition: opacity 250ms ease;
	}
	.step.active .card {
		opacity: 1;
		/* the chips and controls take the pointer; the rest of the layer does not */
		pointer-events: auto;
	}
	.card-title {
		margin: 0 0 6px;
		font-size: 19px;
		line-height: 1.2;
	}
	.card-text {
		margin: 0;
	}

	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
		margin-top: 10px;
	}
	.chip {
		font-family: var(--font-chart);
		font-size: 11.5px;
		font-weight: 800;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--color-ink);
		background: var(--color-paper);
		border: 1px solid rgba(42, 21, 3, 0.18);
		border-radius: 3px;
		padding: 4px 8px;
		cursor: pointer;
		box-shadow: 0 1px 3px rgba(42, 21, 3, 0.14);
		transition:
			transform 120ms ease,
			background 120ms ease;
	}
	.chip .x {
		font: inherit;
		font-size: 12px;
		line-height: 1;
		border: 0;
		background: none;
		color: inherit;
		opacity: 0.55;
		margin-left: 5px;
		padding: 0;
		cursor: pointer;
	}
	.chip .x:hover {
		opacity: 1;
	}
	.chip:hover,
	.chip.on {
		background: var(--color-fox);
		color: #fff;
		border-color: var(--color-fox);
		transform: translateY(-1px);
	}

	.control {
		display: block;
		margin-top: 14px;
	}
	.control-label {
		display: block;
		font-family: var(--font-chart);
		font-size: 11px;
		font-weight: 800;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: rgba(42, 21, 3, 0.65);
		margin-bottom: 6px;
	}
	.control-note {
		display: block;
		font-size: 12px;
		line-height: 1.4;
		color: rgba(42, 21, 3, 0.65);
		margin-top: 4px;
	}
	.control input[type="range"] {
		width: 100%;
		accent-color: var(--color-fox);
		margin: 4px 0 0;
	}
	.control-label b {
		color: var(--color-ink);
	}
	/* the slider's ends: one use on the left, the most-used word on the right */
	.ends {
		display: flex;
		justify-content: space-between;
		font-family: var(--font-chart);
		font-size: 11px;
		color: rgba(42, 21, 3, 0.55);
		margin-top: 2px;
	}
	.control input[type="search"] {
		width: 100%;
		box-sizing: border-box;
		font: inherit;
		font-size: 14px;
		padding: 7px 9px;
		border: 1px solid rgba(42, 21, 3, 0.3);
		border-radius: 3px;
		background: #fff;
		color: var(--color-ink);
	}
	.control input[type="search"]:focus {
		outline: 2px solid var(--color-fox);
		outline-offset: 1px;
	}
	.search-box {
		position: relative;
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
		z-index: 4;
		overflow: hidden;
	}
	.suggest li {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		padding: 7px 10px;
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
		font-family: var(--font-chart);
		font-size: 11px;
		color: rgba(42, 21, 3, 0.55);
	}

	.linger {
		height: 20vh;
	}
	@media (max-width: 860px) {
		.linger {
			height: 70vh;
		}
		.card {
			max-width: 84vw;
		}
		/* card, then its image right underneath */
		.step {
			flex-direction: column;
			justify-content: center;
			gap: 12px;
		}
		.figure {
			position: static;
			transform: none;
			width: 84vw;
			max-height: 40vh;
		}
		/* the explore step: triangle on top, the controls under it */
		.explore .sticky {
			flex-direction: column;
			justify-content: flex-start;
			gap: 8px;
			padding-top: 6px;
			box-sizing: border-box;
		}
		.explore .sticky :global(svg) {
			max-height: 44vh;
		}
		.panel {
			position: static;
			transform: none;
			width: min(660px, 92vw);
			flex: 0 1 auto;
			min-height: 0;
			font-size: 14.5px;
		}
		/* inside a scrolling panel the suggestions sit in flow, not floating */
		.suggest {
			position: static;
			margin-top: 4px;
			box-shadow: none;
		}
	}
	/* the step cards let the pointer through to the chart behind them, but a
	   link in a step's text must still be clickable */
	.steps :global(a) {
		pointer-events: auto;
	}
</style>
