<script>
	// ---------------------------------------------------------------------------
	// The Fightin' Words scatter, walked through in two beats.
	//
	// The full chart is 3,000 words and rewards study; dropped into the middle of
	// an argument it is a wall. So the scrolly holds the same plot still and calls
	// out one set of words at a time — first the fouls, then the race and
	// culture-war vocabulary — with everything else receding rather than
	// disappearing, so the reader can see how far out the called-out words sit.
	//
	// Doc embed:  chart: word-quadrant-scrolly
	// ---------------------------------------------------------------------------
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import WordQuadrant from "$components/WordQuadrant.svelte";

	// The first two beats are the Doc's own sentences; the third hands the chart
	// over — same plot, controls back, nothing dimmed.
	// The Doc owns these words: `chart: word-quadrant-scrolly | steps: wordSteps`.
	let { steps = null } = $props();

	const FALLBACK = [
		{
			words: ["hard", "foul", "fouls", "calls", "flagrant"],
			html: "Case in point: Fox News has consistently discussed &ldquo;<strong>hard</strong>&rdquo; "
				+ "<strong>fouls</strong> against Caitlin Clark more than other outlets."
		},
		{
			words: ["race", "racism", "racist", "privilege", "black", "white"],
			html: "They also invoked <strong>race</strong> and <strong>racism</strong> more than other "
				+ "outlets, as well as culture war buzzwords like &ldquo;<strong>privilege</strong>.&rdquo;"
		},
		{
			words: null,
			explore: true,
			html: "Every word in both archives, and the rest of the controls. Switch between whole "
				+ "articles and headlines, or filter to Caitlin Clark alone."
		}
	];

	const STEPS = $derived(
		steps?.length
			? steps.filter((step) => (step.text ?? "").trim()).map((step) => ({
				words: (step.words ?? "").split(",").map((w) => w.trim()).filter(Boolean),
				explore: step.explore === true || step.explore === "true",
				html: step.text ?? ""
			}))
			: FALLBACK
	);

	let index = $state(0);
	// the sentinel rest-stop past the last card: same chart state as the final
	// beat, but no card on screen — the reader can actually reach the controls
	let current = $derived(STEPS[Math.min(index ?? 0, STEPS.length - 1)] ?? STEPS[0]);
</script>

<section class="wq-scrolly">
	<div class="sticky">
		<!-- whole articles, not headlines: every word in both beats scores two to
		     three times higher in the body text, and "privilege" rests on 34 headline
		     uses against 195 in the articles -->
		<WordQuadrant highlight={current.words} bare controls={current.explore} mode="articles" />
	</div>

	<div class="steps">
		<Scrolly bind:value={index}>
			{#each STEPS as step, i}
				<div class="step" class:active={index === i}>
					<p class="card">{@html step.html}</p>
				</div>
			{/each}
			<!-- a cardless beat at the end: the chart stays sticky one more
			     screen-height with nothing covering the controls -->
			<div class="step step-open" aria-hidden="true"></div>
		</Scrolly>
	</div>
</section>

<style>
	.wq-scrolly { position: relative; margin: 24px 0; }

	.sticky {
		position: sticky; top: 0; height: 100vh;
		display: flex; align-items: center; justify-content: center;
	}
	/* the chart is a flex item, and without this it shrinks to its content */
	.sticky :global(.word-quadrant) { width: min(1000px, 94vw); }
	/* leaves room for the controls the explore beat brings back */
	.sticky :global(svg) { max-height: 74vh; }

	/* the steps ride over the sticky chart, as in the chyron scrolly */
		.steps { position: relative; z-index: 1; margin-top: -100vh; pointer-events: none; }
	.step {
		height: 100vh; display: flex; align-items: center; justify-content: flex-start;
		pointer-events: none;
	}
	.card {
		max-width: 300px; margin: 0;
		background: rgba(255, 253, 248, 0.94);
		border-left: 3px solid #c0392b;
		padding: 14px 16px; border-radius: 3px;
		font-size: 15px; line-height: 1.5; color: #2a1503;
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
		opacity: 0.35; transition: opacity 250ms ease;
	}
	.step.active .card { opacity: 1; }

	@media (max-width: 860px) {
		.sticky { height: 100vh; }
		.steps { margin-top: -100vh; }
		.card { max-width: 84vw; }
	}
</style>
