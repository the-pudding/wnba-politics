<script>
	// Timeline revealed a year at a time; the y-axis rescales to what's on
	// screen, so each new year flattens the ones before it.
	// Doc embed:  chart: timeline-scrolly | words: timeline-trans | steps: transSteps
	import Scrolly from "$components/helpers/Scrolly.svelte";
	import TimelineStatic from "$components/TimelineStatic.svelte";
	import TimelineDots from "$components/TimelineDots.svelte";

	const expand = (value, suffix) => {
		const v = (value ?? "").toString().trim();
		return !v ? null : /^\d{4}$/.test(v) ? v + suffix : v;
	};

	let { steps = null, words = [], title = "", caption = "" } = $props();
	const chartName = $derived(words[0] ?? "timeline-trans");

	const FALLBACK = [
		{ until: "2021-12", text: "Through 2021, Fox almost never writes about trans athletes and the WNBA." },
		{ until: "2022-12", text: "2022 is the Griner year, and it barely moves." },
		{ until: "2023-12", text: "Then 2023: Griner says she'd welcome trans teammates, and Fox platforms Riley Gaines." },
		{ until: "2026-12", text: "And then 2026." }
	];

	const STEPS = $derived(
		steps?.length
			? steps.filter((step) => Object.values(step).some((v) => (v ?? "").toString().trim()))
				.map((step) => ({
				until: (step.until ?? "").trim(),
				// per-beat Doc options: ymax cap; from/to window (bare years expand)
				ymax: (step.ymax ?? "").toString().trim(),
				from: expand(step.from, "-01"),
				to: expand(step.to, "-12"),
				html: step.text ?? ""
			}))
			: FALLBACK
	);

	let index = $state(0);
	let current = $derived(STEPS[index ?? 0] ?? STEPS[0]);
</script>

<section class="timeline-scrolly">
	<div class="sticky">
		<div class="frame">
			{#if title}<h4 class="ts-title">{title}</h4>{/if}
			<!-- "-dots" draws one mark per article; same scrolly contract -->
			{#if chartName.endsWith("-dots")}
				<TimelineDots revealUntil={current.until}
					startMonth={current.from} endMonth={current.to}
					yCap={current.ymax ? +current.ymax : null} tall />
			{:else}
				<TimelineStatic name={chartName} revealUntil={current.until}
					from={current.from} to={current.to}
					yCap={current.ymax ? +current.ymax : null} tall />
			{/if}
			{#if caption}<p class="ts-cap">{caption}</p>{/if}
		</div>
	</div>

	<div class="steps">
		<Scrolly bind:value={index}>
			{#each STEPS as step, i}
				<!-- a textless step is a quiet beat: advances the reveal with no card -->
				<div class="step" class:active={index === i} class:quiet={!step.html.trim()}>
					{#if step.html.trim()}<p class="card">{@html step.html}</p>{/if}
				</div>
			{/each}
		</Scrolly>
	</div>
</section>

<style>
	.timeline-scrolly { position: relative; margin: 24px 0; }

	.sticky {
		position: sticky; top: 0; height: 100vh;
		display: flex; align-items: center; justify-content: center;
	}
	.frame { width: min(880px, 94vw); }
	.ts-title { font-size: 19px; text-align: center; margin: 0 0 8px; color: #2a1503; }
	.ts-cap {
		font-size: 12.5px; line-height: 1.5; color: rgba(42, 21, 3, 0.6);
		text-align: center; max-width: 600px; margin: 10px auto 0;
	}

	.steps { position: relative; z-index: 1; margin-top: -100vh; pointer-events: none; }
	.step { height: 100vh; display: flex; align-items: center; justify-content: flex-start; }
	.step.quiet { height: 55vh; }
	.card {
		max-width: 290px; margin: 0;
		background: rgba(255, 253, 248, 0.94);
		border-left: 3px solid #c0392b;
		padding: 14px 16px; border-radius: 3px;
		font-size: 15.5px; line-height: 1.5; color: #2a1503;
		box-shadow: 0 4px 18px rgba(42, 21, 3, 0.14);
		opacity: 0.3; transition: opacity 250ms ease;
	}
	.step.active .card { opacity: 1; }

	@media (max-width: 860px) { .card { max-width: 84vw; } }

	/* phones: chart rides the top of the screen, card owns the strip below it */
	@media (max-width: 640px) {
		.frame { width: 96vw; }
		.sticky { align-items: flex-start; padding-top: 1vh; }
		.step { align-items: flex-end; justify-content: center; }
		.card { margin-bottom: 2vh; }
	}
</style>
