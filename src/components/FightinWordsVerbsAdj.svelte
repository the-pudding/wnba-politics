<script>
	// Verb-and-adjective scatter walked through
	// Each step takes: who, rel, vs, pair, words, text
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import FightinWords from "$components/FightinWords.svelte";
	import WordBars from "$components/WordBars.svelte";
	import FacePicker from "$components/helpers/FacePicker.svelte";
	import {
		playerWordsSource,
		playerWordsPeople
	} from "../utils/playerWords.js";
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

	// --- the picker: any featured player, any relation, at any step ----------
	// The Doc's steps set it as the reader scrolls; the reader can change it at
	// any time, and the next step sets it again.
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
	$effect(() => {
		const step = current;
		if (step.who && PEOPLE.includes(step.who)) pickedWho = step.who;
		if (step.rel) pickedRel = step.rel;
	});
	// a smaller cast member has too few attachments for some relations; those
	// buttons grey out, and the choice falls back to every word
	let available = $derived(
		new Set(Object.keys(data.players?.[pickedWho]?.vsOutlets ?? {}))
	);
	$effect(() => {
		if (available.size && !available.has(pickedRel)) pickedRel = "all";
	});
	// what the chart shows: the picker's choice; the step's own title, words
	// and pair comparison apply while the choice still matches the step
	let onStep = $derived(pickedWho === current.who && pickedRel === current.rel);
	let shown = $derived(
		onStep
			? current
			: {
					who: pickedWho,
					rel: pickedRel,
					vs: "outlets",
					pair: null,
					words: [],
					title: ""
				}
	);
	let source = $derived(playerWordsSource(shown));
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
						{source.topLabel} <span class="vs">against</span>
						{source.bottomLabel}
					{/if}
				</p>
			</div>
			<!-- the picker, live at every step: the Doc sets it, the reader can change it -->
			<div class="pick">
				<FacePicker names={PICKABLE} bind:value={pickedWho} faceOf={faceUrl} />
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
	.heading {
		font-size: 14.5px;
		color: var(--color-ink);
		text-align: left;
		margin: 0;
		max-width: 460px;
		line-height: 1.35;
	}
	.heading .vs {
		color: rgba(42, 21, 3, 0.55);
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
	.pick-label {
		font-family: var(--font-chart);
		font-size: 11px;
		font-weight: 800;
		letter-spacing: 0.06em;
		text-transform: uppercase;
		color: rgba(42, 21, 3, 0.65);
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
		padding: 5px 10px;
		font-size: 12.5px;
		font-weight: 600;
		cursor: pointer;
	}
	.toggle-group button.active {
		background: var(--color-ink);
		color: #fff;
	}
	.toggle-group button:disabled {
		color: rgba(42, 21, 3, 0.35);
		cursor: not-allowed;
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
		max-width: 300px;
		margin: 0;
		background: rgba(255, 253, 248, 0.94);
		border-left: 3px solid var(--color-fox);
		padding: 14px 16px;
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
</style>
