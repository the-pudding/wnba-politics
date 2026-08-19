<script>
	// ---------------------------------------------------------------------------
	// The verb-and-adjective scatter, walked through.
	//
	// Each beat swaps the whole comparison — a different player, a different
	// grammatical relation, a different opponent — rather than only highlighting
	// different words on one plot. That is the point of the sequence: the same
	// method applied six ways, so the pattern is visibly not an artifact of one
	// cut of the data.
	//
	// The words live in the Doc: chart: player-words-scrolly | steps: wordPlaySteps
	// Each step takes: who, rel, vs, pair, words, text
	//
	// Doc embed:  chart: player-words-scrolly
	// ---------------------------------------------------------------------------
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import WordQuadrant from "$components/WordQuadrant.svelte";
	import { playerWordsSource } from "../utils/playerWords.js";
	import { base } from "$app/paths";
	import faceFiles from "$data/net_faces.json";

	let { steps = null } = $props();

	const FALLBACK = [
		{ who: "Caitlin Clark", rel: "describe", vs: "outlets", words: [],
		  html: "Start with adjectives. This is how Fox describes Caitlin Clark, against how "
		      + "everyone else describes the same player." },
		{ who: "Caitlin Clark", rel: "describe", vs: "pair",
		  pair: "Caitlin Clark vs Angel Reese", words: [],
		  html: "Now Clark against Reese, inside Fox — the comparison Fox's own coverage "
		      + "keeps making." },
		{ who: "Caitlin Clark", rel: "object", vs: "outlets", words: [],
		  html: "Verbs where Clark is the object: what gets done to her. Fox on the left, "
		      + "the rest of the press on the right." },
		{ who: "Sophie Cunningham", rel: "subject", vs: "outlets", words: [],
		  html: "Sophie Cunningham, what she does." },
		{ who: "Sophie Cunningham", rel: "object", vs: "outlets", words: [],
		  html: "And what is done to her." },
		{ who: "DiJonai Carrington", rel: "subject", vs: "outlets", words: [],
		  html: "DiJonai Carrington, what she does." }
	];

	const list = (value) =>
		(value ?? "").split(",").map((w) => w.trim()).filter(Boolean);

	const STEPS = $derived(
		steps?.length
			? steps.filter((step) => (step.text ?? "").trim()).map((step) => ({
				who: (step.who ?? "Caitlin Clark").trim(),
				rel: (step.rel ?? "describe").trim(),
				vs: (step.vs ?? "outlets").trim(),
				pair: (step.pair ?? "").trim() || null,
				words: list(step.words),
				// optional: a Doc-written heading for the sticky, replacing the
				// generated "relation — X against Y" line
				title: (step.title ?? "").trim(),
				html: step.text ?? ""
			}))
			: FALLBACK
	);

	let index = $state(0);
	let current = $derived(STEPS[index ?? 0] ?? STEPS[0]);
	let source = $derived(playerWordsSource(current));
	// the beat changes player as well as measure, so her face rides the heading —
	// six comparisons in a row otherwise blur into one
	const slugOf = (name) =>
		name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
	let faces = $derived(
		(current.vs === "pair" && current.pair
			? current.pair.split(" vs ")
			: [current.who]
		).map((name) => ({ name, file: faceFiles[slugOf(name.trim())], slug: slugOf(name.trim()) }))
	);
</script>

<section class="words-scrolly">
	<div class="sticky">
		{#if source}
			<div class="who">
				{#each faces as face}
					{#if face.file}
						<img src="{base}/net/{face.slug}{face.file}" alt={face.name} />
					{/if}
				{/each}
				<p class="heading">
					{#if current.title}
						{@html current.title}
					{:else}
						<b>{source.relation}</b><br />
						{source.topLabel} <span class="vs">against</span> {source.bottomLabel}
					{/if}
				</p>
			</div>
			<WordQuadrant {source} highlight={current.words} bare controls={false} />
		{:else}
			<p class="heading">No comparison stored for {current.who} · {current.rel}</p>
		{/if}
	</div>

	<div class="steps">
		<Scrolly bind:value={index}>
			{#each STEPS as step, i}
				<div class="step" class:active={index === i}>
					<p class="card">{@html step.html}</p>
				</div>
			{/each}
		</Scrolly>
	</div>
</section>

<style>
	.words-scrolly { position: relative; margin: 24px 0; }

	.sticky {
		position: sticky; top: 0; height: 100vh;
		display: flex; flex-direction: column; align-items: center; justify-content: center;
	}
	.sticky :global(.word-quadrant) { width: min(900px, 96vw); }
	.who {
		display: flex; align-items: center; justify-content: center; gap: 12px;
		margin-bottom: 4px;
	}
	.who img {
		width: 52px; height: 52px; border-radius: 50%; object-fit: cover;
		border: 2px solid rgba(255, 253, 248, 0.9);
		box-shadow: 0 2px 8px rgba(42, 21, 3, 0.18);
	}
	.heading {
		font-size: 14.5px; color: #2a1503; text-align: left;
		margin: 0; max-width: 460px; line-height: 1.35;
	}
	.heading .vs { color: rgba(42, 21, 3, 0.55); }
	.sticky :global(svg) { max-height: 74vh; }

	.steps { position: relative; z-index: 1; margin-top: -100vh; pointer-events: none; }
	.step { height: 100vh; display: flex; align-items: center; justify-content: flex-start; }
	.card {
		max-width: 300px; margin: 0;
		background: rgba(255, 253, 248, 0.94);
		border-left: 3px solid #c0392b;
		padding: 14px 16px; border-radius: 3px;
		font-size: 15.5px; line-height: 1.5; color: #2a1503;
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
		opacity: 0.3; transition: opacity 250ms ease;
	}
	.step.active .card { opacity: 1; }

	@media (max-width: 860px) {
		.card { max-width: 84vw; }
	}
</style>
