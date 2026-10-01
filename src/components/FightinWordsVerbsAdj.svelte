<script>
	// Verb-and-adjective scatter walked through
	// Each step takes: who, rel, vs, pair, words, text
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import FightinWords from "$components/FightinWords.svelte";
	import WordBars from "$components/WordBars.svelte";
	import FacePicker from "$components/helpers/FacePicker.svelte";
	import {
		playerWordsSource,
		playerWordsPeople,
		playerWordsOutlets,
		playerOutletFile
	} from "../utils/playerWords.js";
	import { COMPARISON, LOGO } from "$utils/outlets.js";
	import LogoSelect from "$components/helpers/LogoSelect.svelte";
	import { checks } from "$utils/checks.svelte.js";
	import { base } from "$app/paths";
	import roster from "$data/people.json";
	import data from "$data/player_words.json";
	const faceFiles = Object.fromEntries(
		Object.values(roster)
			.filter((p) => p.face)
			.map((p) => [p.slug, p.face.slice(p.slug.length)])
	);

	// chart: "scatter" (the quadrant) or "bars" (mirrored top words)
	let { steps = null, chart = "scatter", labels = "on", scale = "linear", caps = false, scores = false,
		note = undefined
	} = $props();
	// on a phone the three pickers share one row, so "All other outlets"
	// shortens to "All"
	let narrow = $state(false);
	$effect(() => {
		const mq = window.matchMedia("(max-width: 640px)");
		const sync = () => (narrow = mq.matches);
		sync();
		mq.addEventListener("change", sync);
		return () => mq.removeEventListener("change", sync);
	});

	const list = (value) =>
		(value ?? "")
			.split(",")
			.map((w) => w.trim())
			.filter(Boolean);

	const STEPS = $derived(
		(steps ?? [])
			.filter((step) => (step.text ?? "").trim())
			.map((step) => ({
				who: (step.who ?? "").trim(),
				rel: (step.rel ?? "describe").trim(),
				vs: (step.vs ?? "outlets").trim(),
				pair: (step.pair ?? "").trim() || null,
				words: list(step.words),
				// title: optional Doc heading replacing the generated one
				title: (step.title ?? "").trim(),
				// explore: true — the reader picks the player and the relation
				explore: step.explore === true || step.explore === "true",
				html: step.text ?? ""
			}))
	);

	let index = $state(0);
	// once no card is in view the chart keeps its last state
	let last = $state(0);
	$effect(() => {
		if (index !== undefined && index !== null) last = index;
	});
	let current = $derived(STEPS[last] ?? STEPS[0]);

	
	const RELATIONS = [
		["describe", "how she's described"],
		["play", "how she plays"],
		["subject", "what she does"],
		["object", "what's done to her"],
		["all", "every word"]
	];
	// players with a Fox-versus-the-other-outlets comparison stored, listed
	// by surname in the picker
	const PEOPLE = playerWordsPeople();
	const slugOf = (name) =>
		name
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, "-")
			.replace(/^-|-$/g, "");
	const bySurname = (a, b) =>
		a.split(" ").pop().localeCompare(b.split(" ").pop()) || a.localeCompare(b);
	const PICKABLE = [...PEOPLE].sort(bySurname);
	const faceUrl = (name) => {
		const slug = slugOf(name);
		return faceFiles[slug] ? `${base}/net/${slug}${faceFiles[slug]}` : null;
	};
	let pickedWho = $state(PEOPLE[0] ?? "");
	let pickedRel = $state("describe");
	// "all": Fox against every comparison outlet pooled (the story's chart);
	// an outlet's name: Fox against that outlet alone, to see what each one
	// contributes to the pooled picture
	let pickedOutlet = $state("all");
	$effect(() => {
		const step = current;
		if (step.who && PEOPLE.includes(step.who)) pickedWho = step.who;
		if (step.rel) pickedRel = step.rel;
		pickedOutlet = "all";
	});
	// the outlets with enough of this player's words, in this relation, to
	// stand alone; the rest grey out
	// A check, shown only with ?checks in the address (utils/checks.svelte.js):
	// with or without college coverage. The no-college numbers come from a rerun
	// of notebook 09 with college articles dropped (static/data/nocollege/,
	// 2026-09-30; words only, not two-word phrases).
	let college = $state("with");
	let ncWords = $state(null);
	$effect(() => {
		if (college !== "without" || ncWords) return;
		fetch(`${base}/data/nocollege/src/player_words.json`)
			.then((r) => r.json())
			.then((v) => (ncWords = v))
			.catch(() => {});
	});
	// words, or two-word phrases (each relation's word and its partner in the
	// parse: "foul out", "cheap shot"; notebook 09, 2026-09-30). The phrases
	// ship one file per player (static/data/player_phrases2), fetched on use
	let unit = $state("words");
	let phrases = $derived(unit === "phrases");
	const suffix = (rel) => (phrases ? rel + "2" : rel);
	let phraseFiles = $state({});
	const phraseFetching = new Set();
	$effect(() => {
		const who = pickedWho;
		if (!phrases || !who || phraseFiles[who] || phraseFetching.has(who)) return;
		phraseFetching.add(who);
		fetch(`${base}/data/player_phrases2/${slugOf(who)}.json`)
			.then((r) => (r.ok ? r.json() : {}))
			.catch(() => ({}))
			.then((v) => (phraseFiles = { ...phraseFiles, [who]: v }));
	});
	// the player's block with the phrase relations merged in
	let phraseAlt = $derived.by(() => {
		const f = phraseFiles[pickedWho];
		const base_ = data.players?.[pickedWho];
		if (!phrases || !f || !base_) return null;
		const merged = { ...base_ };
		for (const part of ["relations", "counts", "vsOutlets", "vsCounts", "vsByOutlet"])
			merged[part] = { ...(base_[part] ?? {}), ...(f[part] ?? {}) };
		return { ...data, players: { ...data.players, [pickedWho]: merged } };
	});
	let alt = $derived(phrases ? phraseAlt : college === "without" ? ncWords : null);
	let src_ = $derived(alt ?? data);
	let outletsHere = $derived(new Set(playerWordsOutlets(pickedWho, suffix(pickedRel), alt)));
	$effect(() => {
		if (pickedOutlet !== "all" && !outletsHere.has(pickedOutlet)) pickedOutlet = "all";
	});
	let outlet = $derived(pickedOutlet === "all" ? null : pickedOutlet);
	// a single outlet's comparisons live in one file per player
	// (static/data/player_outlet, notebooks/site_data.py), fetched on first use
	let byOutlet = $state({});
	const fetching = new Set();
	$effect(() => {
		const who = pickedWho;
		const nc = college === "without" && !phrases;
		const k = nc ? `nc:${who}` : who;
		if (!outlet || !who || byOutlet[k] || fetching.has(k)) return;
		fetching.add(k);
		fetch(`${base}/data/${nc ? "nocollege/static/" : ""}${playerOutletFile(who)}`)
			.then((r) => (r.ok ? r.json() : {}))
			.catch(() => ({}))
			.then((block) => (byOutlet = { ...byOutlet, [k]: block }));
	});
	// "all" is the story's own chart; then each comparison outlet on its own
	const OUTLET_OPTIONS = ["all", ...COMPARISON];
	// a smaller cast member has too few attachments for some relations; those
	// buttons grey out, and the choice falls back to every word
	let available = $derived(
		new Set(
			Object.keys(src_?.players?.[pickedWho]?.vsOutlets ?? {})
				.filter((k) => k.endsWith("2") === phrases)
				.map((k) => (phrases ? k.slice(0, -1) : k))
		)
	);
	$effect(() => {
		if (available.size && !available.has(pickedRel)) pickedRel = "all";
	});
	// what the chart shows: the picker's choice; the step's own title, words
	// and pair comparison apply while the choice still matches the step
	let onStep = $derived(pickedWho === current.who && pickedRel === current.rel);
	let shown = $derived(
		onStep
			? { ...current, outlet, title: outlet || phrases ? "" : current.title }
			: {
					who: pickedWho,
					rel: pickedRel,
					vs: "outlets",
					pair: null,
					words: [],
					title: "",
					outlet
				}
	);
	// Fox's column head carries its wordmark; the other side is named in words
	let fresh = $derived.by(() => {
		const src = playerWordsSource({
			...shown,
			rel: suffix(shown.rel),
			byOutlet: byOutlet[college === "without" && !phrases ? `nc:${shown.who}` : shown.who] ?? null,
			alt
		});
		if (!src || shown.vs !== "outlets") return src;
		return { ...src, topLogo: LOGO["Fox News"] };
	});
	// while a picked player's file is still on its way (phrases, a single
	// outlet), the chart keeps showing what it had instead of blinking out
	let waiting = $derived(
		(phrases && !phraseFiles[pickedWho]) ||
			(!!outlet && !byOutlet[college === "without" && !phrases ? `nc:${pickedWho}` : pickedWho] &&
				!data.players?.[pickedWho]?.vsByOutlet?.[suffix(pickedRel)]?.[outlet])
	);
	let lastSource = null;
	let source = $derived.by(() => {
		if (fresh) lastSource = fresh;
		return fresh ?? (waiting ? lastSource : null);
	});
	let faces = $derived(
		(shown.vs === "pair" && shown.pair
			? shown.pair.split(" vs ")
			: [shown.who]
		).map((name) => ({
			name,
			file: faceFiles[slugOf(name.trim())],
			slug: slugOf(name.trim())
		}))
	);
</script>

<section class="words-scrolly" class:bars={chart === "bars"} class:open={index >= STEPS.length}>
	<div class="sticky">
		{#if source}
			<div class="who">
				{#each faces as face}
					{#if face.file}
						<img src="{base}/net/{face.slug}{face.file}" alt={face.name} />
					{/if}
				{/each}
				<p class="heading">
					{#if shown.title}
						{@html shown.title}
					{:else}
						<b>{source.relation}</b><br />
						{source.topLabel} <span class="vs">vs.</span>
						{source.bottomLabel}
					{/if}
				</p>
			</div>
			<!-- the picker, live at every step: the Doc sets it, the reader can change it -->
			<div class="pick">
				<!-- the player and the outlet side by side, labelled fields like the
				     main chart's; the kind of word underneath -->
				<div class="pick-fields">
					<FacePicker names={PICKABLE} bind:value={pickedWho} faceOf={faceUrl} />
					{#if shown.vs === "outlets"}
						<div class="outlet-pick">
							<span class="field-label">Compared with</span>
							<LogoSelect
								options={OUTLET_OPTIONS}
								bind:value={pickedOutlet}
								logoOf={(o) => (o === "all" ? null : LOGO[o] ?? null)}
								nameOf={(o) => (o === "all" ? (narrow ? "All" : "All other outlets") : o)}
								isDisabled={(o) =>
									o !== "all" && !outletsHere.has(o) ? `Too few words about ${pickedWho} in ${o}` : false}
								label="Compared with"
							/>
						</div>
					{/if}
					<div class="outlet-pick words-pick">
						<span class="field-label"># Words</span>
						<div class="ngram-pick" role="group" aria-label="Words at a time">
							{#each ["words", "phrases"] as u, i (u)}
								<button
									type="button"
									class:active={unit === u}
									aria-pressed={unit === u}
									title={u === "words" ? "Single words" : "Two-word phrases"}
									onclick={() => (unit = u)}>{i + 1}</button
								>
							{/each}
						</div>
					</div>
					{#if checks.on}
					<!-- a check: see `college` above -->
					<div class="outlet-pick">
						<span class="field-label">College coverage</span>
						<LogoSelect
							options={["with", "without"]}
							bind:value={college}
							nameOf={(o) => (o === "with" ? "With college" : "Without college")}
							label="College coverage"
						/>
					</div>
					{/if}
				</div>
				<div class="toggle-group" role="group" aria-label="Kind of word">
					{#each RELATIONS as [rel, label] (rel)}
						<button
							class:active={pickedRel === rel}
							disabled={!available.has(rel)}
							title={available.has(rel)
								? ""
								: `Too few ${label.replace("she's", "she is")} words for ${pickedWho}`}
							onclick={() => (pickedRel = rel)}>{label}</button
						>
					{/each}
				</div>
			</div>
			{#if chart === "bars"}
				<WordBars {source} {labels} {scale} {caps} {scores} highlight={shown.words} top={12} fill {note} />
			{:else}
				<FightinWords {source} highlight={shown.words} bare controls={false} />
			{/if}
		{:else}
			<p class="heading">
				No comparison stored for {shown.who} · {shown.rel}
			</p>
		{/if}
	</div>

	<div class="steps">
		<Scrolly bind:value={index}>
			{#each STEPS as step, i}
				<div
					class="step"
					class:active={last === i}
					class:explore={step.explore}
				>
					<p class="card">{@html step.html}</p>
				</div>
			{/each}
			<!-- cardless final beat: the chart stays put for another screen and a
			     half with every card gone, so the reader can pick and hover -->
			<div class="step step-open" aria-hidden="true"></div>
		</Scrolly>
	</div>
</section>

<style>
	.words-scrolly {
		position: relative;
		margin: 24px 0;
	}

	.sticky {
		position: sticky;
		top: 0;
		height: 100vh;
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
	}
	/* the bars hang from a fixed top: a step with more or fewer words only
	   lengthens the chart downward, instead of re-centring everything */
	.words-scrolly.bars .sticky {
		justify-content: flex-start;
		padding-top: 4vh;
		box-sizing: border-box;
	}
	.sticky :global(.fightin-words),
	.sticky :global(.word-bars) {
		width: min(900px, 96vw);
	}
	.who {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 12px;
		margin-bottom: 4px;
	}
	.who img {
		width: 52px;
		height: 52px;
		border-radius: 50%;
		object-fit: cover;
		border: 2px solid rgba(255, 253, 248, 0.9);
		box-shadow: 0 2px 8px rgba(42, 21, 3, 0.18);
	}
	/* two lines held for the heading, so a one-line step title and the
	   two-line generated heading leave the chart in the same place */
	.heading {
		min-height: 2.7em;
		font-size: 14.5px;
		color: var(--color-ink);
		text-align: left;
		margin: 0;
		max-width: 460px;
		line-height: 1.35;
	}
	.heading .vs {
		color: inherit;
	}

	/* the explore step's picker, live above the chart */
	.pick {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 12px;
		flex-wrap: wrap;
		margin: 4px 0 8px;
		pointer-events: auto;
	}
	.pick label {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-size: 13px;
		color: var(--color-ink);
	}
	/* the kinds of word as tabs, like the thread tabs (2026-09-29): sans
	   labels on a heavy ink rule, the open one white and edged in ink */
	/* the rule runs only as wide as the tabs; the row breaks onto its own
	   line under the pickers, which take the full width */
	.toggle-group {
		display: flex;
		flex: 0 0 auto;
		width: fit-content;
		margin: 0 auto;
		justify-content: center;
		/* every tab the row's height, its label centred in it */
		align-items: stretch;
		gap: 2px;
		border-bottom: 2px solid var(--color-ink-dark);
	}
	.toggle-group button {
		display: flex;
		align-items: center;
		justify-content: center;
		text-align: center;
		flex: 0 1 auto;
		/* the tabs stand on the black rule under the row, which shows under each */
		margin-bottom: 0;
		padding: 8px 14px 7px;
		border: 2px solid var(--color-ink-dark);
		border-bottom: 0;
		border-radius: 8px 8px 0 0;
		background: #fff;
		color: var(--color-ink-dark);
		font-family: var(--font-sans);
		font-size: 13.5px;
		font-weight: 700;
		cursor: pointer;
		transition: background 150ms ease;
	}
	.toggle-group button:hover:not(.active):not(:disabled) {
		background: #f2f2f2;
	}
	.toggle-group button.active {
		opacity: 1;
		margin-bottom: 0;
		background: var(--color-ink-dark);
		border-color: var(--color-ink-dark);
		color: #fff;
	}
	/* no ring after a click; a keyboard user still sees which one has focus */
	.toggle-group button:focus-visible {
		outline: none;
		text-decoration: underline;
		text-underline-offset: 3px;
	}
	.toggle-group button:disabled {
		opacity: 0.3;
		cursor: not-allowed;
	}
	/* the outlet dropdown sits beside the player and relation pickers, its
	   label in the face picker's small capitals */
	/* # words: one rounded box split into numbers, the active one filled */
	.ngram-pick {
		display: flex;
		/* only as wide as its buttons, where the field runs the full row (on
		   phones) */
		align-self: flex-start;
		width: max-content;
		height: 38px;
		box-sizing: border-box;
		border: 2px solid var(--color-ink-dark);
		border-radius: 8px;
		overflow: hidden;
		/* ink behind the buttons: where the rounded edge blends, it blends into
		   the border, not a white sliver above the dark button */
		background: var(--color-ink-dark);
	}
	.ngram-pick button {
		appearance: none;
		width: 36px;
		margin: 0;
		padding: 0;
		border: 0;
		border-radius: 0;
		background: #fff;
		color: var(--color-ink-dark);
		font-family: var(--font-sans);
		font-size: 15px;
		font-weight: 600;
		cursor: pointer;
	}
	.ngram-pick button + button {
		border-left: 2px solid var(--color-ink-dark);
	}
	.ngram-pick button.active {
		background: var(--color-ink-dark);
		color: #fff;
	}
	/* no ring after a click; a keyboard user still sees which one has focus */
	.ngram-pick button:focus-visible {
		outline: none;
		text-decoration: underline;
		text-underline-offset: 3px;
	}
	.pick-fields {
		display: flex;
		flex-basis: 100%;
		justify-content: center;
		align-items: flex-end;
		flex-wrap: wrap;
		gap: 12px 14px;
	}
	.outlet-pick {
		display: inline-flex;
		flex-direction: column;
		gap: 5px;
	}
	.field-label {
		font-family: var(--font-sans);
		font-size: 13px;
		font-weight: 600;
		color: var(--color-ink-dark);
	}
	/* on a phone the pickers shrink to the bars' scale, as on the main chart */
	@media (max-width: 640px) {
		.pick-fields {
			gap: 8px;
		}
		/* player, outlet and number of words on one row: the two pickers
		   share what the buttons leave */
		.pick-fields {
			flex-wrap: nowrap;
		}
		.pick-fields > :global(*) {
			flex: 1 1 0;
			min-width: 0;
		}
		.pick-fields > .words-pick {
			flex: 0 0 auto;
		}
		/* a player's name needs more room than an outlet's */
		.pick-fields > :global(.face-picker) {
			flex-grow: 1.45;
		}
		.field-label,
		.pick-fields :global(.pick-label) {
			font-size: 11.5px;
		}
		/* the number buttons at the dropdowns' phone height */
		.ngram-pick {
			height: 32px;
			border-radius: 6px;
		}
		.ngram-pick button {
			width: 32px;
			font-size: 13.5px;
		}
		.pick-fields :global(.face-picker .current),
		.pick-fields :global(.logo-select .current) {
			width: 100%;
			min-width: 0;
			height: 32px;
			border-radius: 6px;
			font-size: 13px;
		}
		.pick-fields :global(.logo-select),
		.pick-fields :global(.face-picker) {
			width: 100%;
		}
		.pick-fields :global(.face-picker img),
		.pick-fields :global(.face-picker .blank) {
			width: 22px;
			height: 22px;
		}
		/* the kinds of word: the full width, smaller type, two lines at most */
		.toggle-group {
			display: flex;
			width: 100%;
		}
		.toggle-group button {
			flex: 1 1 0;
			min-width: 0;
			padding: 6px 3px 5px;
			font-size: 11.5px;
			line-height: 1.15;
		}
	}
	/* the bars size their own rows to the viewport; the scatter is capped */
	.words-scrolly:not(.bars) .sticky :global(svg) {
		max-height: 74vh;
	}

	.steps {
		position: relative;
		z-index: 1;
		margin-top: -100vh;
		pointer-events: none;
	}
	.step {
		height: 100vh;
		display: flex;
		align-items: center;
		justify-content: flex-start;
	}
	.card {
		/* wider only where the screen leaves a margin beside the 900px chart */
		max-width: clamp(300px, calc((100vw - 900px) / 2 - 24px), 380px);
		margin: 0;
		background: rgba(255, 253, 248, 0.94);
		border-left: 3px solid var(--color-fox);
		padding: 14px 16px;
		border-radius: 3px;
		font-size: var(--step-text);
		line-height: 1.5;
		color: var(--color-ink);
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
		opacity: 0.3;
		transition: opacity 250ms ease;
	}
	.step.active .card {
		opacity: 1;
	}
	.step-open {
		height: 150vh;
	}
	/* on the open beat the cards leave the chart alone */
	.words-scrolly.open .card {
		opacity: 0;
	}
	/* the explore card keeps out of the chart's way */
	.step.explore {
		align-items: flex-end;
		padding-bottom: 6vh;
		box-sizing: border-box;
	}

	@media (max-width: 860px) {
		.card {
			max-width: 84vw;
		}
	}
	/* the step cards let the pointer through to the chart behind them, but a
	   link in a step's text must still be clickable */
	.steps :global(a) {
		pointer-events: auto;
	}
</style>
