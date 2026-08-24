<script>
	// Verb-and-adjective scatter walked through: each beat swaps the whole
	// comparison (player, relation, opponent), not just the highlighted words.
	// Doc embed:  chart: player-words-scrolly | steps: wordPlaySteps
	// Each step takes: who, rel, vs, pair, words, text
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import FightinWords from "$components/FightinWords.svelte";
	import { playerWordsSource } from "../utils/playerWords.js";
	import { base } from "$app/paths";
	import roster from "$data/people.json";
	const faceFiles = Object.fromEntries(
		Object.values(roster).filter((p) => p.face)
			.map((p) => [p.slug, p.face.slice(p.slug.length)]));

	let { steps = null } = $props();


	const list = (value) =>
		(value ?? "").split(",").map((w) => w.trim()).filter(Boolean);

	const STEPS = $derived(
		(steps ?? []).filter((step) => (step.text ?? "").trim()).map((step) => ({
				who: (step.who ?? "").trim(),
				rel: (step.rel ?? "describe").trim(),
				vs: (step.vs ?? "outlets").trim(),
				pair: (step.pair ?? "").trim() || null,
				words: list(step.words),
				// title: optional Doc heading replacing the generated one
				title: (step.title ?? "").trim(),
				html: step.text ?? ""
			}))
	);

	let index = $state(0);
	let current = $derived(STEPS[index ?? 0] ?? STEPS[0]);
	let source = $derived(playerWordsSource(current));
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
			<FightinWords {source} highlight={current.words} bare controls={false} />
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
	.sticky :global(.fightin-words) { width: min(900px, 96vw); }
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
		font-size: 14.5px; color: var(--color-ink); text-align: left;
		margin: 0; max-width: 460px; line-height: 1.35;
	}
	.heading .vs { color: rgba(42, 21, 3, 0.55); }
	.sticky :global(svg) { max-height: 74vh; }

	.steps { position: relative; z-index: 1; margin-top: -100vh; pointer-events: none; }
	.step { height: 100vh; display: flex; align-items: center; justify-content: flex-start; }
	.card {
		max-width: 300px; margin: 0;
		background: rgba(255, 253, 248, 0.94);
		border-left: 3px solid var(--color-fox);
		padding: 14px 16px; border-radius: 3px;
		font-size: 15.5px; line-height: 1.5; color: var(--color-ink);
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
		opacity: 0.3; transition: opacity 250ms ease;
	}
	.step.active .card { opacity: 1; }

	@media (max-width: 860px) {
		.card { max-width: 84vw; }
	}
</style>
